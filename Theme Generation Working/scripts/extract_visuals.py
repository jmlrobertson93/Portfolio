"""
Walks a Power BI PBIP report's /definition/pages tree and catalogues every
visual's formatting (`objects` / `visualContainerObjects`) into a single
reference file, grouped by visualType.

Why this exists: a theme JSON's `visualStyles.<visualType>.*.<card>` uses
PLAIN values (`"show": false`, `"fontSize": 12`, `{"solid": {"color": "#fff"}}`).
A PBIR visual.json wraps the same properties in DAX-literal expressions
(`{"expr": {"Literal": {"Value": "false"}}}`, `14D`, `'Arial'`) and encodes
colours as theme-palette references (`ThemeDataColor`). This script decodes
the DAX-literal wrapper back to plain values so the output can be compared
directly against theme JSON syntax, while leaving ThemeDataColor references
annotated (since those are intentionally NOT literal colours).

Usage:
    python scripts/extract_visuals.py "<Report>.Report" reference/visual_catalogue

Outputs:
    <out>.json  - machine-readable, one record per visual
    <out>.md    - human-readable, grouped by visualType, deduped per card/property
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict


def decode_literal(raw: str):
    """Decode a DAX literal string (as found in expr.Literal.Value) to a plain Python value."""
    if raw is None:
        return None
    s = raw.strip()
    if s == "true":
        return True
    if s == "false":
        return False
    if s == "null":
        return None
    # Quoted string literal: 'Arial'
    m = re.fullmatch(r"'(.*)'", s, re.DOTALL)
    if m:
        return m.group(1)
    # Long integer: 0L, 2026L
    m = re.fullmatch(r"(-?\d+)L", s)
    if m:
        return int(m.group(1))
    # Double: 14D, 0.5D
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)D", s)
    if m:
        return float(m.group(1))
    # Fallback: return raw string, flagged, so nothing is silently lost
    return {"__raw_literal__": raw}


def decode_value_node(node):
    """Recursively decode an 'objects' subtree, resolving expr.Literal wrappers
    and annotating ThemeDataColor / FillRule / Aggregation expressions that
    have no plain-value equivalent."""
    if isinstance(node, dict):
        if "expr" in node and isinstance(node["expr"], dict):
            expr = node["expr"]
            if "Literal" in expr:
                return decode_literal(expr["Literal"].get("Value"))
            if "ThemeDataColor" in expr:
                tdc = expr["ThemeDataColor"]
                return {"__theme_color__": f"dataColors[{tdc.get('ColorId')}]", "percent": tdc.get("Percent", 0)}
            if "Aggregation" in expr or "Column" in expr or "Measure" in expr:
                return {"__data_bound__": True}
            # Unknown expression kind - keep raw for inspection
            return {"__raw_expr__": expr}
        return {k: decode_value_node(v) for k, v in node.items()}
    if isinstance(node, list):
        return [decode_value_node(v) for v in node]
    return node


def decode_objects(objects: dict):
    """Decode a full `objects` (or `visualContainerObjects`) node: card -> [instances]."""
    if not objects:
        return {}
    decoded = {}
    for card, instances in objects.items():
        decoded_instances = []
        for inst in instances:
            entry = {}
            if "properties" in inst:
                entry["properties"] = {
                    prop: decode_value_node(val) for prop, val in inst["properties"].items()
                }
            if "selector" in inst:
                entry["selector"] = inst["selector"]
            if "$id" in inst:
                entry["$id"] = inst["$id"]
            decoded_instances.append(entry)
        decoded[card] = decoded_instances
    return decoded


def extract_title(visual_container_objects_decoded: dict):
    title_card = visual_container_objects_decoded.get("title")
    if title_card:
        text = title_card[0].get("properties", {}).get("text")
        if isinstance(text, str):
            return text
    return None


def walk_report(report_dir: Path, page_filter: str = None):
    pages_dir = report_dir / "definition" / "pages"
    records = []
    page_names = {}
    for page_dir in sorted(pages_dir.iterdir()):
        if not page_dir.is_dir():
            continue
        page_json = page_dir / "page.json"
        display_name = page_dir.name
        if page_json.exists():
            pj = json.loads(page_json.read_text(encoding="utf-8"))
            display_name = pj.get("displayName", page_dir.name)
        page_names[page_dir.name] = display_name

        if page_filter and display_name.strip() != page_filter.strip():
            continue

        visuals_dir = page_dir / "visuals"
        if not visuals_dir.exists():
            continue
        for visual_dir in sorted(visuals_dir.iterdir()):
            vjson_path = visual_dir / "visual.json"
            if not vjson_path.exists():
                continue
            vj = json.loads(vjson_path.read_text(encoding="utf-8"))
            visual = vj.get("visual", {})
            visual_type = visual.get("visualType", "<unknown>")
            objects_decoded = decode_objects(visual.get("objects", {}))
            vco_decoded = decode_objects(visual.get("visualContainerObjects", {}))
            title = extract_title(vco_decoded)

            records.append({
                "page": display_name,
                "pageId": page_dir.name,
                "visualId": visual_dir.name,
                "visualType": visual_type,
                "title": title,
                "position": vj.get("position"),
                "objects": objects_decoded,
                "visualContainerObjects": vco_decoded,
                "sourcePath": str(vjson_path.relative_to(report_dir.parent)),
            })
    return records


def build_markdown(records):
    by_type = defaultdict(list)
    for r in records:
        by_type[r["visualType"]].append(r)

    lines = ["# Visual Formatting Catalogue", ""]
    lines.append(f"Extracted {len(records)} visuals across "
                 f"{len(set(r['pageId'] for r in records))} pages, "
                 f"{len(by_type)} distinct visualType values.")
    lines.append("")
    lines.append("**Decode legend:** `__theme_color__` = bound to a theme palette slot "
                  "(`dataColors[n]`), not a literal colour. `__data_bound__` = bound to a "
                  "field/measure, not themeable. `__raw_literal__` / `__raw_expr__` = value "
                  "the decoder didn't recognise — inspect manually.")
    lines.append("")

    for vtype in sorted(by_type.keys()):
        instances = by_type[vtype]
        lines.append(f"## {vtype}  ({len(instances)} instance{'s' if len(instances) != 1 else ''})")
        lines.append("")
        lines.append("| Page | Title | visualId |")
        lines.append("|---|---|---|")
        for inst in instances:
            lines.append(f"| {inst['page']} | {inst['title'] or ''} | `{inst['visualId']}` |")
        lines.append("")

        # Merge cards/properties seen across all instances of this type.
        # `objects` (visual-specific: axes, labels, legend...) and
        # `visualContainerObjects` (chrome: title, background, divider, border,
        # padding...) both land in the SAME `visualStyles.<type>.*` namespace in
        # a theme file, so they're merged here into one flat card list to match.
        # Container-level cards are tagged [container] since that's useful to know
        # when deciding what's visual-specific vs shared chrome.
        cards = defaultdict(lambda: defaultdict(list))  # card -> property -> [values]
        for inst in instances:
            for card, card_instances in inst["objects"].items():
                for ci in card_instances:
                    for prop, val in ci.get("properties", {}).items():
                        cards[card][prop].append({
                            "value": val,
                            "visualId": inst["visualId"],
                            "title": inst["title"],
                            "selector": ci.get("selector"),
                        })
            for card, card_instances in inst["visualContainerObjects"].items():
                for ci in card_instances:
                    for prop, val in ci.get("properties", {}).items():
                        cards[f"[container] {card}"][prop].append({
                            "value": val,
                            "visualId": inst["visualId"],
                            "title": inst["title"],
                            "selector": ci.get("selector"),
                        })

        if not cards:
            lines.append("_No `objects` formatting set on any instance (default formatting)._")
            lines.append("")
            continue

        lines.append("**Cards / properties observed:**")
        lines.append("")
        for card in sorted(cards.keys()):
            lines.append(f"- **{card}**")
            for prop in sorted(cards[card].keys()):
                seen = cards[card][prop]
                # De-dupe identical values for compact display
                uniq = []
                for s in seen:
                    key = json.dumps(s["value"], sort_keys=True, default=str)
                    if key not in [json.dumps(u["value"], sort_keys=True, default=str) for u in uniq]:
                        uniq.append(s)
                value_strs = []
                for u in uniq:
                    tag = f" (`{u['visualId']}`" + (f" \"{u['title']}\"" if u['title'] else "") + ")"
                    sel = f" [selector: {u['selector']}]" if u.get("selector") else ""
                    value_strs.append(f"`{json.dumps(u['value'])}`{sel}{tag}")
                lines.append(f"  - `{prop}`: " + "; ".join(value_strs))
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) not in (3, 4):
        print("Usage: python extract_visuals.py <ReportName.Report> <output_basename> [page_display_name]")
        sys.exit(1)

    report_dir = Path(sys.argv[1])
    out_base = Path(sys.argv[2])
    page_filter = sys.argv[3] if len(sys.argv) == 4 else None
    out_base.parent.mkdir(parents=True, exist_ok=True)

    records = walk_report(report_dir, page_filter)

    out_json = out_base.with_suffix(".json")
    out_json.write_text(json.dumps(records, indent=2), encoding="utf-8")

    out_md = out_base.with_suffix(".md")
    out_md.write_text(build_markdown(records), encoding="utf-8")

    print(f"Extracted {len(records)} visuals.")
    print(f"  -> {out_json}")
    print(f"  -> {out_md}")


if __name__ == "__main__":
    main()
