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

Copy the required script `src` values exactly. Do not alter, decode, re-encode, or reconstruct
the URLs.

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
- For meter-gated, cooldown-gated, charged, rare, super, or ultimate abilities, still include them as gameplay actions. Use a semantic action_id such as `super`, `ultimate`, or `charged-special`; set behavior=discrete and interaction=tap when activation is one-shot.
- Include all important player gameplay actions even when there are many; the library owns overflow placement for rare discrete actions.
- If two actions are symmetric opposites (rotate left/right, previous/next, zoom in/out, lane up/down), map them to secondary + tertiary and set pair_id + pair_position (left/right).
- Required keyboard state-transition controls are must-map utility actions. If a key is needed to start, resume, continue, pause, unpause, open/close a menu, retry/restart, or play again, map it to the `pause` action.
- State-transition controls include Pause, Start, Resume, Continue, Retry/Restart, Play Again, Unpause, and Menu toggles.
- Do this even when there is no explicit `pause` variable and even when the key only matters outside active gameplay: if a key transitions between game states (menu, intro, paused, game over, victory, round end), classify it as `pause`.
- Do not omit a required state-transition key because the gameplay action cluster is full; `pause` renders in the utility area outside the main cluster.
- Only omit state-transition keys when the transition is already reachable through a visible click/touch UI and the keyboard key is merely optional.
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
- If the code has jump semantics (for example jump force, jump velocity, double jump, can-jump, grounded-jump checks, or a function/variable named jump), always include that key as jump with behavior=discrete and interaction=tap. Do this even if the key was also considered for an axis; the library can then resolve the duplicate deterministically.
- Prefer not to duplicate a discrete/impulse/action key inside an axis. A key belongs in an axis only when holding it continuously controls the same movement variable as the other directions in that axis.
- If movement direction is only set on keydown (no keyup handling) or movement continues after a tap, set activation=latch and direction_mode=cardinal (even if movement is continuous).
- If diagonals are not meaningful or only one direction is intended at a time, set direction_mode=cardinal.
- If a core action requires holding two directions together with independent timing, split into rate + magnitude axes and set simultaneous=true on those axes.
- If direction_mode=cardinal or activation=latch, directions are mutually exclusive, so set simultaneous=false (or omit it).
- If multiple keys map to the same action, pick the primary and mention alternates in notes.
- Never put multiple key codes in one string. Invalid: `"KeyF, ShiftRight"`. Use exactly one KeyboardEvent.code string for each action, or a JSON array such as `["KeyF", "ShiftRight"]` only when the control should press both keys at the same time.
- For same-keyboard local multiplayer games, build touch controls for one player only unless explicitly asked for two-player touch controls. Prefer player 1 / primary / WASD controls, and mention player 2 controls in notes. Do not combine player 1 and player 2 keys into one action array.
- Use key arrays only for a true same-player chord where one touch control must press multiple keys at once. Do not use arrays for alternate keys, mirrored player controls, or player 2 controls.
