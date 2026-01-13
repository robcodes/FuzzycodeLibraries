# Touchpad Controls Library Vision

## Goal
Build a drop-in JS library (CDN script) that makes keyboard-only web games playable on touch devices.
The library should let us define on-screen controls that emit synthetic keyboard events so existing
game code keeps working without rewrites. Later, we will auto-generate layouts from game HTML using
an LLM, but the library must own all ergonomics and layout logic so the LLM only maps game actions
to control roles.

## Current Demo Baseline (`examples/demo.html`)
The demo already proves the core mechanics:
- `createTouchpadControls` builds button and joystick controls.
- Controls emit synthetic `keydown` / `keyup` events to the canvas or document.
- Multiple layouts are supported: safe platformer, fast platformer, dual-stick, runner.
- NippleJS is used for joysticks and directional pads.

This demo is the reference for the API shape and the UX we want to keep polishing.

## Core Principles
- Zero game code changes: add a CDN script and inject a layout config.
- Predictable input: keys are pressed/released exactly as a keyboard would do.
- Fast on low-end devices: minimal DOM, no heavy frameworks.
- Ergonomic defaults: controls placed for two-thumb grip and reachability.
- Clear iconography: buttons show role/key-derived glyphs (arrows/shapes) without manual labeling.
- Layouts derive from input topology (axes, action count, simultaneity), not genre names.
- Responsive and orientation-aware: works on phones/tablets, portrait/landscape.
- Non-invasive: respects safe areas and avoids blocking non-control UI elements.

## Deterministic Bridge (layer responsibilities)
- LLM: extract keys and label universal semantics (no placement decisions).
- Update script: validate and normalize the schema to deterministic enums.
- Library: choose layout, placement, and ergonomics based on semantics.

## First-Principles Layout Rules (library-owned)
These are defaults the LLM should never have to decide.
### Input topology (what the game needs)
- Movement axis count: none, one-axis (left/right), or two-axis (left/right/up/down).
- Independent aim axis: separate keys from movement imply two-thumb aiming.
- Action taxonomy: primary/secondary/tertiary actions, plus modifiers (run, dash, block).
- Action type: hold vs tap, and whether actions must be held simultaneously.
- Simultaneous demands: if two inputs must be held while another is tapped, split across thumbs.

### Ergonomics (how the player holds the device)
- Thumbs rest in bottom corners; anchors should sit ~15-20% from left/right edges and ~10-15% from
  the bottom, adjusted for `env(safe-area-inset-*)`.
- Movement controls belong to the left thumb by default. Actions belong to the right thumb.
- Two-button actions should form a gentle arc; primary action is the largest and most reachable.
- D-pad for discrete precision; joystick for analog or continuous directional control.
- Avoid accidental diagonal or vertical input when only horizontal control is required.
- If more than two actions must be held together, split across thumbs.
- Minimum touch target: 48px, ideal 64-96px depending on device size.
- Provide a comfort margin so controls do not sit on the very edge (reduce accidental swipes).
- Scale sizes based on viewport min(width, height), not fixed pixels.

## Action Semantics (LLM-provided, library-consumed)
The library cannot infer intent from code, so the LLM should label each action with universal
semantics. This avoids genre-specific overfitting while still yielding good placement.

Definitions:
- discrete: a one-shot impulse or state change on press (jump, dash, toggle, interact).
- continuous: effect persists while held (movement, aim, charge, sustained fire).
- axis: two-directional or four-directional control where diagonals may matter.
- button: single action that is tapped or held.
- control_space: the semantic space the control belongs to:
  - vector: true 2D direction (axes form a single directional intent).
  - rate: heading/steering change (left/right).
  - magnitude: advance/drive/accelerate (often one direction).
- activation: how input stays active:
  - hold: active only while pressed.
  - latch: tap sets direction/state until changed; no need to hold.
- direction_mode: whether diagonals are meaningful:
  - vector: diagonals are meaningful.
  - cardinal: only one direction at a time.
- granularity: spatial resolution of movement:
  - fine: small, continuous increments.
  - coarse: large, quantized steps (tiles/lanes).
- interaction: tap (single press), hold (sustained), or repeat (rapid taps).
- simultaneous:
  - for axes: multiple directions are commonly held together during core play.
  - for actions: the action is commonly held while other actions are used (movement + fire).
- pair_id / pair_position (actions only): link symmetric pairs (rotate left/right, zoom in/out)
  so the library can place them side-by-side (`pair_position`: `left` or `right`).

These semantics drive layout choice and spacing but do not choose absolute positions.

## Layout Archetypes (input-topology based)
These are first-class templates the library can choose based on bindings.
- `safe-platformer`: one-axis movement + 1-2 actions (horizontal-only movement pad).
- `fast-platformer`: two-axis movement + 1-2 actions (full D-pad).
- `dual-stick`: independent movement axis + independent aim axis + 1 action.
- `runner`: no movement axis + three large actions in a bottom band.

Names are shorthand and not genre-specific. Each preset exposes sensible defaults for size, spacing,
and placement and can be lightly overridden via config.

## Layout Selection Heuristics (library-owned)
- If `aim` exists, choose a dual-axis layout with two thumbs.
- If `move` has only left/right, choose a horizontal-only pad to avoid accidental vertical input.
- If `move` has up/down, choose a full D-pad or joystick (based on precision vs analog need).
- If no `move` exists, choose a bottom band or right-thumb cluster based on action count.
- If a modifier must be held while moving, place it on the opposite thumb.

## Action-Semantic Heuristics (library-owned)
- If an action is discrete and commonly simultaneous with movement, put it on the right thumb.
- If an action is continuous and must be held, make it larger and closer to the thumb anchor.
- If Up is discrete (jump), do not include it in the movement axis; expose it as a button.
- If vertical is continuous (true up/down movement), keep it on the movement axis.
- If left/right are rate control and advance is magnitude control, do not couple them as a vector.
- If a core action requires holding two directions together with independent timing, split into
  separate rate/magnitude axes; do not leave a single cardinal axis.
- If an aim axis exists, keep movement left and aim right, then place fire above/near aim.
- If two actions are symmetric opposites, map them to `secondary` + `tertiary` and set
  `pair_id` / `pair_position` so they render side-by-side.

## Current Placement Heuristics (implementation notes)
- Base movement size: clamp(minDim * 0.17, 64, 112).
- Action size: clamp(minDim * 0.14, 56, 96); small action: clamp(minDim * 0.12, 48, 80).
- Edge padding: clamp(minDim * 0.05, 16, 32); spacing: clamp(minDim * 0.03, 10, 20).
- Minimum touch target: 48px (aligned with common mobile touch target guidance).
- Anchor Y: bottom safe area minus padding minus half size, lifted slightly by orientation.

## Library API (proposed stable surface)
The library should keep a simple, composable API with a stable JSON shape.

Example integration:
```html
<script src="https://cdn.fuzzycode.ai/touchpad-controls.min.js"></script>
<script>
  TouchpadControls.create({
    layout: "auto",
    bindings: {
      move: { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" },
      jump: "Space",
      secondary: "KeyJ"
    },
    actionMeta: {
      move: {
        kind: "axis",
        control_space: "vector",
        behavior: "continuous",
        interaction: "hold",
        granularity: "fine",
        simultaneous: true
      },
      jump: { kind: "button", behavior: "discrete", interaction: "tap", simultaneous: true }
    },
    debug: false
  });
</script>
```
Set `debug: true` to log the computed layout summary to the console.

Optional theme (all fields optional; defaults are already tuned):
```js
TouchpadControls.create({
  theme: {
    iconColor: "#E2E8F0",
    iconOpacity: 0.9,
    iconScale: 0.52,
    labelMode: "none", // none | text | key | both
    labelColor: "#E2E8F0",
    labelSize: 12,
    background: "radial-gradient(135% 135% at 25% 20%, rgba(255,255,255,0.15), rgba(0,0,0,0.6))",
    backgroundImage: "url(https://example.com/texture.png)",
    backgroundBlend: "soft-light",
    backgroundSize: "cover",
    backgroundPosition: "center",
    foregroundImage: "url(https://example.com/icon.png)",
    foregroundOpacity: 0.8,
    foregroundSize: "60%",
    foregroundBlend: "normal"
  }
});
```
You can also override theme per button with `buttons[].theme`.

Example lower-level layout override:
```js
TouchpadControls.create({
  layout: "custom",
  buttons: [
    { id: "move", type: "joystick", role: "move", keys: { left: "A", right: "D", up: "W", down: "S" } },
    { id: "jump", type: "button", role: "jump", keys: "Space" }
  ],
  theme: "glass",
  safeArea: true
});
```

## LLM Integration Contract (concise and unambiguous)
The LLM reports keys and semantics; the update script normalizes this into the library’s
`bindings` + `actionMeta`. The LLM never chooses positions or sizes.
If multiple axes exist for the same `usage`, mark the most important as `priority: "primary"`
and any additional as `priority: "secondary"`. The update script will map at most two axes to
left/right controls deterministically.

Required output schema:
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
    },
    {
      "usage": "aim",
      "priority": "primary",
      "control_space": "vector",
      "keys": { "left": "KeyJ", "right": "KeyL", "up": "KeyI", "down": "KeyK" },
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
    "primary": { "keys": "KeyJ", "behavior": "continuous", "interaction": "hold", "simultaneous": true },
    "secondary": {
      "keys": "KeyQ",
      "behavior": "discrete",
      "interaction": "tap",
      "simultaneous": false,
      "pair_id": "rotate",
      "pair_position": "left"
    },
    "tertiary": {
      "keys": "KeyW",
      "behavior": "discrete",
      "interaction": "tap",
      "simultaneous": false,
      "pair_id": "rotate",
      "pair_position": "right"
    },
    "modifier": { "keys": "ShiftLeft", "behavior": "continuous", "interaction": "hold", "simultaneous": true }
  },
  "notes": "optional short text for edge cases"
}
```

The runtime uses this to select a preset and wire keys. Any ergonomics remain library logic.

The library also accepts the analysis schema (`axes` + `actions`) directly and will normalize it
into `bindings` + `actionMeta` at runtime. This lets prompt-only edits still work if they inject
the analysis shape.

## Prompt Sources (keep in sync)
The canonical LLM prompt is `prompts/pipeline_prompt_template.md` (used by the Python pipeline).
Manual edit prompts (`prompts/update_tab_prompt_bindings.md`, `prompts/update_tab_prompt_analysis.md`) must mirror the same schema and rules;
only the injection instructions should differ. This prevents drift between the Python and
prompt-only flows.

## End-to-End Flow
1. Fetch game HTML.
2. LLM analyzes key usage and returns the bindings JSON.
3. Inject CDN script + bindings JSON into the page.
4. Library renders controls and emits keyboard events.
5. Optional: user can toggle controls or switch layouts on demand.

## Success Criteria
- Zero regressions for keyboard users.
- Touch control latency feels instantaneous.
- Layouts are comfortable across devices without manual tuning.
- The LLM prompt is short and deterministic, with a minimal schema.
