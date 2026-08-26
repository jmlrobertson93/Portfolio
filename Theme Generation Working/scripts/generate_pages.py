"""
Generates new report pages that replicate the chrome (title bar, KPI banner,
10 filter slicers, metadata footer, help icons) of the "Design Template
Examples" page, swapping only the 4 main visualisation slots for a new set
of Power BI visual types each time - so that across all generated pages,
every core visual type gets represented at least once.

Chrome visuals are copied VERBATIM from the source page (fresh GUID names
only - position, query bindings, and any formatting are untouched), so
slicers/KPI banner/metadata behave identically on every page. The 4 main
visuals are newly built per page from real fields in the semantic model,
left UNFORMATTED (no objects/visualContainerObjects) so they're "clean"
visuals for theme testing.

Usage:
    python scripts/generate_pages.py
"""

import json
import secrets
from pathlib import Path

REPORT_DIR = Path(__file__).parent.parent / "Theme Experimenting - Spotify.Report"
PAGES_DIR = REPORT_DIR / "definition" / "pages"
SOURCE_PAGE_ID = "1d7922ae23530dc6062c"  # "Design Template Examples"

# The 4 main-viz visual IDs on the source page, in slot order:
# top-left, top-right, bottom-left, bottom-right
MAIN_VIZ_IDS = [
    "9ac8352418edcb245a50",  # Bar / Column Example -> top-left slot
    "d84eab88261488839a60",  # Line Chart Example -> top-right slot
    "86046915e2884d6a68cb",  # Pie Chart Example -> bottom-left slot
    "d027b16c496f248d7594",  # Matrix Example -> bottom-right slot
]

VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.8.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"

# Page-background image (structural-blue title band + white canvas) that
# replaced the "Title Background Example" shape - confirmed structure read
# back from a manually-saved test page. "Fit" is the internal literal for
# what Desktop's formatting pane labels "Stretch".
PAGE_BACKGROUND_OBJECTS = {
    "background": [
        {
            "properties": {
                "image": {
                    "image": {
                        "name": {"expr": {"Literal": {"Value": "'page_background.png'"}}},
                        "url": {
                            "expr": {
                                "ResourcePackageItem": {
                                    "PackageName": "RegisteredResources",
                                    "PackageType": 1,
                                    "ItemName": "page_background025602956681401112.png",
                                }
                            }
                        },
                        "scaling": {"expr": {"Literal": {"Value": "'Fit'"}}},
                    }
                },
                "transparency": {"expr": {"Literal": {"Value": "0D"}}},
            }
        }
    ]
}


def new_id():
    return secrets.token_hex(10)


def col(entity, prop):
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }


def measure(entity, prop):
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }


def qstate(**roles):
    return {role: {"projections": fields} for role, fields in roles.items()}


# (page displayName, [ (visualType, queryState roles dict), x4 ])
# Confidence flag noted inline - HIGH = well-established role names,
# LOWER = best-effort, worth checking the field landed in the right well.
PAGES = [
    ("2 - Bar & Column Charts", [
        ("barChart", qstate(
            Category=[col("dim_platform", "Platform Category")],
            Series=[col("fact_stream", "shuffle")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("columnChart", qstate(
            Category=[col("dim_calendar", "Year")],
            Series=[col("fact_stream", "skipped")],
            Y=[measure("_Measures", "Listening Time (hrs)")],
        )),
        ("clusteredColumnChart", qstate(
            Category=[col("dim_platform", "Platform Category")],
            Y=[measure("_Measures", "Count of Streams"), measure("_Measures", "Unique Tracks")],
        )),
        ("hundredPercentStackedBarChart", qstate(
            Category=[col("dim_calendar", "Year")],
            Series=[col("dim_platform", "Platform Category")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
    ]),
    ("3 - Bar & Column Charts II", [
        ("hundredPercentStackedColumnChart", qstate(
            Category=[col("dim_calendar", "Year")],
            Series=[col("fact_stream", "shuffle")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("stackedBarChart", qstate(
            Category=[col("dim_platform", "Platform Category")],
            Series=[col("fact_stream", "skipped")],
            Y=[measure("_Measures", "Listening Time (hrs)")],
        )),
        ("stackedColumnChart", qstate(
            Category=[col("dim_calendar", "Year")],
            Series=[col("fact_stream", "shuffle")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("waterfallChart", qstate(  # LOWER confidence: skipped "Breakdown" role
            Category=[col("dim_calendar", "Year")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
    ]),
    ("4 - Area & Combo Charts", [
        ("areaChart", qstate(
            Category=[col("dim_calendar", "Calendar Date")],
            Y=[measure("_Measures", "Listening Time (hrs)")],
        )),
        ("stackedAreaChart", qstate(
            Category=[col("dim_calendar", "Calendar Date")],
            Series=[col("fact_stream", "shuffle")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("lineClusteredColumnComboChart", qstate(  # LOWER confidence: Y2 role
            Category=[col("dim_calendar", "Year")],
            Y=[measure("_Measures", "Count of Streams")],
            Y2=[measure("_Measures", "Avg. Stream Duration (min)")],
        )),
        ("lineStackedColumnComboChart", qstate(  # LOWER confidence: Y2 role
            Category=[col("dim_calendar", "Year")],
            Series=[col("fact_stream", "shuffle")],
            Y=[measure("_Measures", "Count of Streams")],
            Y2=[measure("_Measures", "Avg. Stream Duration (min)")],
        )),
    ]),
    ("5 - Other Cartesian", [
        ("ribbonChart", qstate(
            Category=[col("dim_calendar", "Year")],
            Series=[col("dim_platform", "Platform Category")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("funnel", qstate(
            Category=[col("dim_playback_reason", "Reason Name")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("scatterChart", qstate(  # LOWER confidence: role names for X/Y/Size
            Category=[col("dim_artist", "Artist Name")],
            X=[measure("_Measures", "Avg. Stream Duration (min)")],
            Y=[measure("_Measures", "Count of Streams")],
            Size=[measure("_Measures", "Unique Tracks")],
        )),
        ("donutChart", qstate(
            Category=[col("dim_platform", "Platform Category")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
    ]),
    ("6 - Part-to-Whole & Cards", [
        ("treemap", qstate(  # LOWER confidence: "Group" role name
            Group=[col("dim_artist", "Artist Name")],
            Values=[measure("_Measures", "Count of Streams")],
        )),
        ("multiRowCard", qstate(
            Values=[
                measure("_Measures", "Count of Streams"),
                measure("_Measures", "Unique Artists"),
                measure("_Measures", "Unique Albums"),
                measure("_Measures", "Listening Time (hrs)"),
            ],
        )),
        ("gauge", qstate(  # LOWER confidence: no Min/Max/Target bound
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("kpi", qstate(  # LOWER confidence: role names for Indicator/TrendLine
            Indicator=[measure("_Measures", "Count of Streams")],
            TrendLine=[col("dim_calendar", "Year")],
        )),
    ]),
    ("7 - Tables & Maps", [
        ("pivotTable", qstate(
            Rows=[col("dim_calendar", "Year")],
            Columns=[col("dim_platform", "Platform Category")],
            Values=[measure("_Measures", "Count of Streams")],
        )),
        ("map", qstate(  # LOWER confidence: role name for bubble size
            Category=[col("dim_country", "Country Code")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("filledMap", qstate(  # LOWER confidence
            Category=[col("dim_country", "Country Code")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
        ("shapeMap", qstate(  # LOWER confidence: default shape map key may not match ISO country codes
            Category=[col("dim_country", "Country Code")],
            Y=[measure("_Measures", "Count of Streams")],
        )),
    ]),
]


def load_chrome_templates():
    """Every visual on the source page except the 4 main-viz slots."""
    visuals_dir = PAGES_DIR / SOURCE_PAGE_ID / "visuals"
    templates = []
    for vdir in sorted(visuals_dir.iterdir()):
        if vdir.name in MAIN_VIZ_IDS:
            continue
        vjson = json.loads((vdir / "visual.json").read_text(encoding="utf-8"))
        templates.append(vjson)
    return templates


def load_main_viz_positions():
    positions = []
    for vid in MAIN_VIZ_IDS:
        vjson = json.loads((PAGES_DIR / SOURCE_PAGE_ID / "visuals" / vid / "visual.json").read_text(encoding="utf-8"))
        positions.append(vjson["position"])
    return positions


def write_visual(page_dir: Path, visual_json: dict):
    vid = visual_json["name"]
    vdir = page_dir / "visuals" / vid
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "visual.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")


def main():
    chrome_templates = load_chrome_templates()
    main_positions = load_main_viz_positions()

    # Rename the source page to "1 - Examples"
    source_page_json_path = PAGES_DIR / SOURCE_PAGE_ID / "page.json"
    source_page_json = json.loads(source_page_json_path.read_text(encoding="utf-8"))
    source_page_json["displayName"] = "1 - Examples"
    source_page_json_path.write_text(json.dumps(source_page_json, indent=2), encoding="utf-8")
    print(f"Renamed source page -> '1 - Examples'")

    new_page_ids = []

    for display_name, viz_specs in PAGES:
        page_id = new_id()
        new_page_ids.append(page_id)
        page_dir = PAGES_DIR / page_id
        page_dir.mkdir(parents=True, exist_ok=True)

        page_json = {
            "$schema": PAGE_SCHEMA,
            "name": page_id,
            "displayName": display_name,
            "displayOption": "FitToPage",
            "height": 1080,
            "width": 1920,
            "objects": PAGE_BACKGROUND_OBJECTS,
        }
        (page_dir / "page.json").write_text(json.dumps(page_json, indent=2), encoding="utf-8")

        # Copy chrome verbatim with fresh GUIDs
        for template in chrome_templates:
            v = json.loads(json.dumps(template))  # deep copy
            v["name"] = new_id()
            write_visual(page_dir, v)

        # Build the 4 main-viz slots
        for (visual_type, query_state), position in zip(viz_specs, main_positions):
            v = {
                "$schema": VISUAL_SCHEMA,
                "name": new_id(),
                "position": dict(position),
                "visual": {
                    "visualType": visual_type,
                    "query": {"queryState": query_state},
                    "drillFilterOtherVisuals": True,
                },
            }
            write_visual(page_dir, v)

        print(f"Created page '{display_name}' ({page_id}): "
              f"{len(chrome_templates)} chrome + {len(viz_specs)} main visuals")

    # Update pages.json: insert new pages right after the source page
    pages_json_path = PAGES_DIR / "pages.json"
    pages_json = json.loads(pages_json_path.read_text(encoding="utf-8"))
    order = pages_json["pageOrder"]
    idx = order.index(SOURCE_PAGE_ID)
    pages_json["pageOrder"] = order[:idx + 1] + new_page_ids + order[idx + 1:]
    pages_json_path.write_text(json.dumps(pages_json, indent=2), encoding="utf-8")
    print(f"\nUpdated pages.json - inserted {len(new_page_ids)} pages after '1 - Examples'")


if __name__ == "__main__":
    main()
