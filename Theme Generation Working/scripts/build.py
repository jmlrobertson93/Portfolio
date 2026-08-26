"""
Merges every partial in /src into a single dist/theme.json.

Merge rule: plain recursive dict merge. Dict values merge key-by-key; any
other value (including lists, since card definitions are single-instance
arrays like "title": [ {...} ]) from a later file REPLACES the earlier
value entirely - partials are not expected to define the same card twice,
so an overwrite is printed as a heads-up in case that ever happens by
accident.

Files are processed in sorted filename order, so _tokens.json and
_global.json (leading underscore) merge first, then per-visual-type
partials layer their visualStyles.<type> blocks on top.

A partial may instead be a MULTI-TYPE partial: several unrelated Power BI
visual types (e.g. barChart, columnChart, clusteredColumnChart) that all
want the identical card block, to avoid hand-duplicating the same JSON
into one file per type. Shape:

    {
      "_appliesTo": ["barChart", "columnChart", "clusteredColumnChart"],
      "styles": { "*": { ...cards... } }
    }

The build expands this into visualStyles.<type>.* for every type listed,
using the same "styles" content for each, before merging normally.

Usage:
    python scripts/build.py
"""

import json
from pathlib import Path

SRC_DIR = Path(__file__).parent.parent / "src"
DIST_DIR = Path(__file__).parent.parent / "dist"
OUT_FILE = DIST_DIR / "theme.json"


def deep_merge(base: dict, incoming: dict, path: str = ""):
    for key, value in incoming.items():
        full_path = f"{path}.{key}" if path else key
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value, full_path)
        else:
            if key in base and base[key] != value:
                print(f"  overwrite: {full_path}")
            base[key] = value
    return base


def expand_multi_type(partial: dict) -> dict:
    """Turn a {"_appliesTo": [...], "styles": {...}} partial into a normal
    {"visualStyles": {type1: {...}, type2: {...}, ...}} partial."""
    types = partial["_appliesTo"]
    styles = partial["styles"]
    return {"visualStyles": {t: styles for t in types}}


def main():
    src_files = sorted(SRC_DIR.glob("*.json"))
    if not src_files:
        print(f"No .json files found in {SRC_DIR}")
        return

    theme = {}
    for f in src_files:
        partial = json.loads(f.read_text(encoding="utf-8"))
        if "_appliesTo" in partial:
            print(f"merging {f.name} (multi-type: {', '.join(partial['_appliesTo'])})")
            partial = expand_multi_type(partial)
        else:
            print(f"merging {f.name}")
        deep_merge(theme, partial, path="")

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(theme, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_FILE} ({len(src_files)} partials merged)")


if __name__ == "__main__":
    main()
