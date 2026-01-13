# Touchpad Controls: Project Overview

This repo builds a drop-in JS library and tooling that makes keyboard-only web games playable on
touch devices. The core idea is simple: render on-screen controls that emit synthetic keyboard
events so existing game logic works unchanged.

The project is designed for Fuzzycode: kids make games on desktop, but we want one-click (or
auto) conversion so those games play well on tablets/phones after publishing.

## Philosophy (first principles)
- **No genre rules**. Layouts derive from input topology + ergonomics, not "platformer" or
  "shooter" labels.
- **Deterministic bridge**. The LLM only labels semantics; the library owns layout/placement.
- **Thumb ergonomics first**. Two-thumb grip, safe areas, and reachability determine placement.
- **Zero game code edits**. We only inject scripts/config; game logic stays intact.
- **Predictable input**. Touch events must map to keydown/keyup exactly like a keyboard.

## Layers and responsibilities
1) **LLM extraction (nondeterministic)**  
   - Reads HTML/JS and outputs **semantic** control info.
2) **Update script (deterministic normalization)**  
   - Validates enums and applies conservative fallbacks.
3) **Library (deterministic layout + input)**  
   - Chooses layouts, sizes, and positions based on semantics.
4) **Runtime detection (DOM-aware heuristics)**  
   - Detects existing touch UI or safe-area changes.

More detail: `docs/LAYERING_LOGIC.md`

## Canonical schema (analysis)
The canonical LLM output is the **analysis schema**. It is the single source of truth for
control semantics and is used by both the Python pipeline and the JS runtime.

Minimal example (actual output should include only used fields):
```json
{
  "layout": "auto",
  "axes": [
    {
      "usage": "movement",
      "priority": "primary",
      "control_space": "vector",
      "keys": { "left": "ArrowLeft", "right": "ArrowRight", "up": "ArrowUp", "down": "ArrowDown" },
      "behavior": "continuous",
      "interaction": "hold",
      "activation": "hold",
      "direction_mode": "vector",
      "granularity": "fine",
      "simultaneous": true
    }
  ],
  "actions": {
    "jump": { "keys": "Space", "behavior": "discrete", "interaction": "tap", "simultaneous": true },
    "primary": { "keys": "KeyJ", "behavior": "continuous", "interaction": "hold", "simultaneous": true }
  }
}
```

### Key semantics (LLM provides; library uses)
- **control_space**: `vector` (2D direction), `rate` (heading/steer), `magnitude` (drive/advance).
- **behavior**: `continuous` (changes while held), `discrete` (step/impulse).
- **activation**: `hold` (active only while pressed), `latch` (tap sets state/direction).
- **direction_mode**: `vector` (diagonals meaningful), `cardinal` (one direction at a time).
- **granularity**: `fine` (pixel/velocity), `coarse` (tile/lane jumps).
- **simultaneous**:
  - axes: directions are commonly held together during core play.
  - actions: action often held while other actions are used.
- **pair_id / pair_position** (actions): link symmetric pairs for side-by-side layout.

## Layout logic (library-owned)
- **Dual-stick** if an independent `aim` axis exists.
- **Digital D-pad** when movement is cardinal/latch/discrete/coarse or diagonals are not meaningful.
- **Joystick** when movement is vector/continuous/fine and diagonals matter.
- **Axis decoupling**: if rate (heading) and magnitude (drive) are independent, split them into
  separate controls; never couple them as a single 2D stick.
- **Paired actions**: if `pair_id` is present on `secondary`/`tertiary`, render them side-by-side
  above the primary action for ergonomic symmetry.

See: `docs/TOUCHPAD_LIBRARY_VISION.md`, `docs/ANALYSIS_AXIS_DECOUPLING.md`

## Input formats supported
The library accepts either:
- **analysis schema** (`axes` + `actions`)
- **flat bindings** (`bindings` + `actionMeta`)

The runtime normalizes analysis input into bindings/actionMeta so prompt-only edits can work
without the Python pipeline.

## Prompts (keep in sync)
The **canonical** prompt lives at:
- `prompts/prompt_template.md` (used by the Python script)

Prompt-only editing (same semantics, different injection instructions):
- `prompts/prompt.md` (inject flat bindings/actionMeta)
- `prompts/prompt_analysis.md` (inject analysis schema directly)

Rule: the semantics/rules section must stay identical to the canonical prompt. Only the
injection instructions differ.
CDN note: prompts currently reference `http://aws.fuzzycode.dev/fuzzycode_assets/touchpad-controls.js?v2`
for cache busting.

## Tooling and workflows
### 1) Automated pipeline (preferred)
`update_to_auto_touchpad_support.py` runs the LLM and injects controls:
```bash
python3 update_to_auto_touchpad_support.py --game examples/game1.html --embed-lib
```
Outputs:
- `<game>_touch.html` (external touchpad-controls.js)
- `<game>_touch_embedded.html` (embedded library)

This script uses `prompts/prompt_template.md` and records runs in `llm_runs/`.
It supports Groq (`openai/gpt-oss-120b`) or Codex (`gpt-5.1-codex-mini`), and reads `GROQ_API_KEY`
from `.env` (current or parent directory).

### 2) Prompt-only editing
Use `prompts/prompt.md` or `prompts/prompt_analysis.md` when applying edits manually (e.g., update tab).

## Testing and regression
- `scripts/validate_layouts.js`: sanity checks layout bounds/sizes.
- `scripts/run_testcases.py`: runs LLM on stored HTMLs.
- `test_cases/`: game snapshots, embedded outputs, gold standards, and case notes.

Gold standards:
- `test_cases/gold_standard_configs/` (configs)
- `test_cases/gold_standard_layouts/` (computed layouts)
- `test_cases/CASE_NOTES.md` (manual evaluation notes)

## Known limitations / open cases
From `test_cases/CASE_NOTES.md`:
- Mouse-only games need touch-to-mouse support (virtual cursor).
- Typing games need full keyboard overlay or input focus handling.
- Games with existing touch UI should be detected and avoided.
- Contextual actions (restart/pause) should be labeled as utility to avoid prime space.
- Extremely complex games (RTS) likely require a different UX or skip.

## Key files
- `touchpad-controls.js`: library runtime.
- `update_to_auto_touchpad_support.py`: LLM pipeline + injector.
- `examples/demo.html`: visual demo of the library.
- `docs/TOUCHPAD_LIBRARY_VISION.md`: detailed vision + heuristics.
- `docs/LAYERING_LOGIC.md`: deterministic layering principles.
