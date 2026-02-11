# Page Audits (OpenRouter)

Run single-page HTML audits directly against OpenRouter from Python.

## Script
- `run_openrouter_game_audit.py`

## Example (Neon Shift, cheapest provider routing)
```bash
python3 FuzzycodeLibraries/page_audits/run_openrouter_game_audit.py \
  --html-file FuzzycodeLibraries/.auditdata/top20_games_full_context_audit_2026-02-11/pages/02_a002edcd2740_neon-shift-the-weaver/original.html \
  --out-file FuzzycodeLibraries/page_audits/runs/neon_shift.audit.json \
  --raw-file FuzzycodeLibraries/page_audits/runs/neon_shift.raw.json \
  --model openai/gpt-oss-120b \
  --provider-sort price
```

## Key behavior
- Reads `OPENROUTER_API_KEY` from:
  1. process env, or
  2. repository root `.env`
- Sends full HTML source in one request.
- Writes parsed JSON audit output and optional raw response.
- Uses OpenRouter provider routing with `sort=price` by default.
