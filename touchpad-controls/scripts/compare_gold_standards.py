#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare current outputs/layouts against gold standards."
    )
    parser.add_argument(
        "--outputs-dir",
        default="test_cases/outputs/top_voted",
        help="Directory containing embedded outputs."
    )
    parser.add_argument(
        "--gold-config-dir",
        default="test_cases/gold_standard_configs",
        help="Directory containing gold config JSON files."
    )
    parser.add_argument(
        "--current-layouts",
        default="test_cases/layout_snapshots/top_voted_layouts.json",
        help="Current layout snapshot JSON."
    )
    parser.add_argument(
        "--gold-layouts",
        default="test_cases/gold_standard_layouts/top_voted_good_layouts.json",
        help="Gold layout snapshot JSON."
    )
    parser.add_argument(
        "--list",
        default="test_cases/gold_standard_good_list.txt",
        help="List of gold-standard games to compare."
    )
    return parser.parse_args()


def load_list(path: Path) -> List[str]:
    lines = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def extract_json(content: str, name: str) -> Optional[Dict[str, Any]]:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*([\s\S]*?);", content)
    if not match:
        return None
    return json.loads(match.group(1))


def extract_layout(content: str) -> str:
    match = re.search(r'layout:\\s*"([^"]+)"', content)
    return match.group(1) if match else "auto"


def normalize_config(layout: str, bindings: Dict[str, Any], action_meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "layout": layout or "auto",
        "bindings": bindings or {},
        "action_meta": action_meta or {}
    }


def compare_dicts(current: Dict[str, Any], gold: Dict[str, Any]) -> List[str]:
    diffs = []
    keys = set(current.keys()) | set(gold.keys())
    for key in sorted(keys):
        if key not in current:
            diffs.append(f"missing:{key}")
            continue
        if key not in gold:
            diffs.append(f"extra:{key}")
            continue
        if current[key] != gold[key]:
            diffs.append(f"changed:{key}")
    return diffs


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    outputs_dir = (root / args.outputs_dir).resolve()
    gold_config_dir = (root / args.gold_config_dir).resolve()
    current_layouts_path = (root / args.current_layouts).resolve()
    gold_layouts_path = (root / args.gold_layouts).resolve()
    list_path = (root / args.list).resolve()

    names = load_list(list_path)
    if not names:
        print("No games found in list.", file=sys.stderr)
        sys.exit(1)

    current_layouts = json.loads(current_layouts_path.read_text())
    gold_layouts = json.loads(gold_layouts_path.read_text())

    config_matches = []
    config_mismatches = []
    layout_matches = []
    layout_mismatches = []
    missing_outputs = []
    missing_gold = []

    for name in names:
        output_file = outputs_dir / f"{name}_touch_embedded.html"
        gold_config_file = gold_config_dir / f"{name}_config.json"

        if not output_file.exists():
            missing_outputs.append(name)
            continue
        if not gold_config_file.exists():
            missing_gold.append(name)
            continue

        content = output_file.read_text()
        bindings = extract_json(content, "touchBindings")
        action_meta = extract_json(content, "touchActionMeta") or {}
        layout = extract_layout(content)
        if bindings is None:
            config_mismatches.append((name, ["missing:bindings"]))
        else:
            current_config = normalize_config(layout, bindings, action_meta)
            gold_raw = json.loads(gold_config_file.read_text())
            gold_config = normalize_config(
                gold_raw.get("layout", "auto"),
                gold_raw.get("bindings", {}),
                gold_raw.get("action_meta") or gold_raw.get("actionMeta") or {}
            )
            diff = compare_dicts(current_config, gold_config)
            if diff:
                config_mismatches.append((name, diff))
            else:
                config_matches.append(name)

        current_game = current_layouts.get("games", {}).get(name)
        gold_game = gold_layouts.get("games", {}).get(name)
        if not current_game or not gold_game:
            layout_mismatches.append((name, ["missing:layout_snapshot"]))
            continue

        current_viewports = current_game.get("layouts", {})
        gold_viewports = gold_game.get("layouts", {})
        viewport_diffs = []
        for viewport_name, gold_layout in gold_viewports.items():
            current_layout = current_viewports.get(viewport_name)
            if current_layout is None:
                viewport_diffs.append(f"missing:{viewport_name}")
                continue
            if current_layout != gold_layout:
                viewport_diffs.append(f"changed:{viewport_name}")

        if viewport_diffs:
            layout_mismatches.append((name, viewport_diffs))
        else:
            layout_matches.append(name)

    print("Config matches:", len(config_matches), "/", len(names))
    if config_mismatches:
        print("Config mismatches:")
        for name, diff in config_mismatches:
            print(f"  - {name}: {', '.join(diff)}")
    if missing_outputs:
        print("Missing outputs:", ", ".join(missing_outputs))
    if missing_gold:
        print("Missing gold configs:", ", ".join(missing_gold))

    print("\nLayout matches:", len(layout_matches), "/", len(names))
    if layout_mismatches:
        print("Layout mismatches:")
        for name, diff in layout_mismatches:
            print(f"  - {name}: {', '.join(diff)}")


if __name__ == "__main__":
    main()
