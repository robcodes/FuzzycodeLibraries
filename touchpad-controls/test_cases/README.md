# Touchpad Test Cases

This folder contains local HTML snapshots extracted from the pages dataset plus gold standards and layout snapshots.
Generated outputs live under `outputs/` but are gitignored.

## Structure
- `games/`: Source HTML files (one per game).
- `outputs/`: Embedded touchpad outputs generated from each game (gitignored).
- `gold_standard_configs/`: Known-good injected configs for regression testing.
- `gold_standard_layouts/`: Known-good constructed layouts for regression testing.
- `gold_standard_good_list.txt`: List of outputs accepted as good (used to refresh gold files).
- `gold_standard_update_list.txt`: Subset of gold standards to refresh after re-runs.
- `layout_snapshots/`: JSON layout snapshots used for regression comparisons.
- `layout_renders/`: Rendered SVG/PNG layouts for quick visual inspection.
- `index.json`: Mapping from requested titles to matched pages.
- `top_voted_index.json`: Mapping for the top-voted API import.
- `CASE_NOTES.md`: Observations and follow-ups from manual testing.

## Generate embedded outputs
Run from the repository root (outputs are generated locally and not tracked):

```bash
python3 scripts/run_testcases.py
```

Optional:
```bash
python3 scripts/run_testcases.py --provider codex
python3 scripts/run_testcases.py --games-dir test_cases/games/top_voted --output-dir test_cases/outputs/top_voted --allow-empty
python3 scripts/run_testcases.py --dry-run
```

## Refresh gold standards
Make sure you have generated outputs first:
```bash
node scripts/export_gold_configs.js --input-dir test_cases/outputs/top_voted --list test_cases/gold_standard_good_list.txt
node scripts/export_layout_snapshots.js --input-dir test_cases/outputs/top_voted --output test_cases/gold_standard_layouts/top_voted_good_layouts.json --list test_cases/gold_standard_good_list.txt
```

## Render layout SVGs (optional PNG)
```bash
python3 scripts/render_layout_snapshots.py --input test_cases/layout_snapshots/top_voted_layouts.json --output-dir test_cases/layout_renders
python3 scripts/render_layout_snapshots.py --input test_cases/layout_snapshots/top_voted_layouts.json --output-dir test_cases/layout_renders --list test_cases/gold_standard_good_list.txt --png
```
