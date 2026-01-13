# Gold Standard Layouts

These JSON files capture the constructed layouts (buttons + metrics) derived from the library for
known-good games. They let us regression-test the output even when the config schema changes.

Generate:
```bash
node scripts/export_layout_snapshots.js --input-dir test_cases/outputs/top_voted --output test_cases/gold_standard_layouts/top_voted_good_layouts.json --list test_cases/gold_standard_good_list.txt
```
