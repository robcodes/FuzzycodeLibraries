# Gold Standard Configs

These JSON files capture the injected `layout`, `bindings`, and `action_meta` for games that
currently behave perfectly. They are intended for regression testing: if future changes alter
these configs unexpectedly, it is a signal to review LLM prompt or layout logic changes.

The current good list lives in `test_cases/gold_standard_good_list.txt`. Use
`scripts/export_gold_configs.js` to refresh these configs from embedded outputs.

Configs moved out of the active list are stored in `test_cases/gold_standard_configs/archive`.
