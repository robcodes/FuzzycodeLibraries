Use this "{{TOUCHPAD_LIBRARY_URL}}" to add touchpad controls to the game.

You are editing a single-page HTML game. Your job:
1) Identify the keyboard controls used by the game.
2) Inject touchpad controls so the game works on touch devices without changing game logic.

Rules:
- Do NOT rewrite gameplay code. Only add the touchpad scripts + config.
- Insert scripts before the closing </body>.
- Ensure nipplejs is loaded before touchpad-controls.js.
- If TouchpadControls.create already exists, update its config instead of adding a duplicate.
- Use KeyboardEvent.code values (KeyW, ArrowUp, Space, Escape, etc).
- If the game has no keyboard controls, still insert the scripts but use empty axes/actions (axes: [], actions: {}).
- Keep defaults: do not set theme unless explicitly needed.

Required script tags to inject:
<script src="{{NIPPLEJS_CDN_URL}}" crossorigin="anonymous"></script>
<script src="{{TOUCHPAD_LIBRARY_URL}}"></script>

Then inject a config block like this (fill in bindings/actionMeta from your analysis):
<script>
  const touchBindings = {
    move: { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" },
    jump: "Space",
    primary: "KeyJ",
    secondary: "KeyQ",
    tertiary: "KeyW",
    modifier: "ShiftLeft",
    pause: "Escape",
    magnitude: "ArrowUp"
  };
  const touchActionMeta = {
    move: {
      behavior: "continuous",
      interaction: "hold",
      activation: "hold",
      direction_mode: "vector",
      granularity: "fine",
      simultaneous: true
    },
    jump: { behavior: "discrete", interaction: "tap", simultaneous: true },
    primary: { behavior: "continuous", interaction: "hold", simultaneous: true }
  };
  TouchpadControls.create({
    layout: "auto",
    bindings: touchBindings,
    actionMeta: touchActionMeta
  });
</script>

Touchpad config schema (deterministic JSON):
{
  "layout": "auto",
  "axes": [
    {
      "usage": "movement",
      "priority": "primary",
      "control_space": "vector",
      "keys": { "left": "KeyA", "right": "KeyD", "up": "KeyW", "down": "KeyS" },
      "behavior": "continuous",
      "interaction": "hold",
      "activation": "hold",
      "direction_mode": "vector",
      "granularity": "fine",
      "simultaneous": true
    }
  ],
  "actions": {
    "jump": { "keys": "Space", "action_id": "jump", "behavior": "discrete", "interaction": "tap", "simultaneous": true },
    "primary": { "keys": "KeyJ", "action_id": "primary-attack", "behavior": "continuous", "interaction": "hold", "simultaneous": true },
    "secondary": {
      "keys": "KeyQ",
      "action_id": "rotate-left",
      "behavior": "discrete",
      "interaction": "tap",
      "simultaneous": false,
      "pair_id": "rotate",
      "pair_position": "left"
    },
    "tertiary": {
      "keys": "KeyW",
      "action_id": "rotate-right",
      "behavior": "discrete",
      "interaction": "tap",
      "simultaneous": false,
      "pair_id": "rotate",
      "pair_position": "right"
    },
    "modifier": { "keys": "ShiftLeft", "action_id": "sprint", "behavior": "continuous", "interaction": "hold", "simultaneous": true },
    "pause": { "keys": "Escape", "action_id": "pause-menu", "behavior": "discrete", "interaction": "tap", "simultaneous": false },
    "magnitude": { "keys": "ArrowUp", "action_id": "thrust", "behavior": "continuous", "interaction": "hold", "simultaneous": true }
  },
  "notes": "optional short note"
}

Important:
- The JSON schema above is for *analysis*. You must translate it into `bindings` + `actionMeta`.
- If you are unsure about a control, omit it rather than guessing.

Rules for axes/actions (apply from first principles):
- Use axes only for directional or rate controls; use actions for single-key controls.
- actions keys must be one of: jump, primary, secondary, tertiary, modifier, pause, magnitude.
- Every action object must include `action_id` as a semantic slug (lowercase `a-z`, `0-9`, `_`, `-`), e.g. `kick`, `special`, `dash-attack`, `pause-menu`.
- `action_id` should describe gameplay meaning (what it does), not physical position (`left-button`, `right-button`) and not generic role names unless semantics are truly unknown.
- If two actions are symmetric opposites (rotate left/right, previous/next, zoom in/out, lane up/down), map them to secondary + tertiary and set pair_id + pair_position (left/right).
- Treat high-level state-transition controls as utility pause/start semantics and map them to the `pause` action.
- State-transition controls include Pause, Start, Resume, Continue, Retry/Restart, Play Again, Unpause, and Menu toggles.
- Do this even when there is no explicit `pause` variable: if a key is only used to transition between game states (menu, intro, paused, game over, victory, round end), classify it as `pause`.
- Choose an `action_id` that matches the transition meaning (for example `pause-menu`, `start-menu`, `resume-game`, `restart-round`, `play-again`).
- Use movement for heading/rotation and forward/back drive controls. Use aim only for a separate targeting axis.
- control_space values:
  - vector: true 2D direction (diagonals are meaningful).
  - rate: heading/steering change (left/right).
  - magnitude: advance/drive/accelerate (often one direction).
- behavior values:
  - continuous: state changes smoothly while input is active.
  - discrete: state changes in fixed steps; holding just repeats steps.
- activation:
  - hold: active only while pressed.
  - latch: a tap sets direction/state until changed; no need to hold.
- direction_mode:
  - vector: diagonals are meaningful.
  - cardinal: only one direction at a time.
- granularity:
  - fine: small, continuous increments (pixel/velocity integration).
  - coarse: large, quantized steps (grid/tile/lane jumps).
- If movement is step-based (grid/tile/turn), set behavior=discrete and interaction=tap or repeat.
- If movement direction is only set on keydown (no keyup handling) or movement continues after a tap, set activation=latch and direction_mode=cardinal (even if movement is continuous).
- If diagonals are not meaningful or only one direction is intended at a time, set direction_mode=cardinal.
- If a core action requires holding two directions together with independent timing, split into rate + magnitude axes and set simultaneous=true on those axes.
- If direction_mode=cardinal or activation=latch, directions are mutually exclusive, so set simultaneous=false (or omit it).
- If multiple keys map to the same action, pick the primary and mention alternates in notes.
