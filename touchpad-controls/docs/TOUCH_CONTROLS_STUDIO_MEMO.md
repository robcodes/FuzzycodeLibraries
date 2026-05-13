# Touch Controls Studio Memo

## Purpose

Touch controls should become a first-class editable surface, not only an AI-generated snippet. The same customization system should work in two contexts:

- Published pages, where players can customize controls for themselves at play time.
- The FuzzyCode editor, where creators can customize controls and persist the result back into the project HTML.

The touchpad library should own the optional customization/editor layer because it already owns rendered controls, layout decisions, roles, action IDs, overflow rules, safe areas, utility buttons, and skinning. FuzzyCode should own the editor-time shell, asset picking, versioning, and persistence.

## Current System

FuzzyCode currently has a fast-change path through `/apply_action_fast`. It sends the current HTML plus the user request to SimpleGPT, asks for search/replace blocks, applies them server-side, and prewarms literal asset URLs.

The touchpad fast prompt is loaded from the vendored `update_tab_prompt_analysis.md` and hydrated with:

- `{{TOUCHPAD_LIBRARY_URL}}`
- `{{NIPPLEJS_CDN_URL}}`

The touchpad library currently supports:

- `TouchpadControls.create(config)`
- auto layout from `axes` and `actions`
- deterministic duplicate axis/action handling
- utility pause/top-strip handling
- overflow handling for rare actions
- `skin` for image and style customization, including `skin.roles`, `skin.actions`, and `skin.joystick`

The missing capability is a live editor/customizer API.

## Product Shape

When touch controls are not installed:

- The current fast touchpad button can open an "Add Touch Controls" flow.
- AI detects keyboard controls and inserts a first-pass `TouchpadControls.create(...)` config.
- The touch controls editor opens so the user can resolve ambiguity visually.

When touch controls are already installed:

- The same entry becomes "Edit Touch Controls".
- It opens the library editor using the existing config.
- The user can adjust included actions, main vs rare/utility actions, button images, role/action mappings, size/opacity, and possibly positions.
- In FuzzyCode editor mode, a "Save to project" action persists the changed config into the HTML.

## Library Ownership

The library should expose an optional editor/customizer API. Possible shape:

```js
const controls = TouchpadControls.create(config);

controls.openEditor({
  mode: "play",
  assetPicker,
  onChange,
  onSave
});
```

or:

```js
TouchpadControls.openEditor({
  config,
  mode: "editor",
  assetPicker,
  onSave
});
```

In published pages, `onSave` should persist to local browser storage. These player preferences should not modify the published page for other users.

In the FuzzyCode editor, `onSave` should send the updated config to the parent editor shell so it can create a new project version.

## Persistence Options

AI persistence is easier initially because it can reuse `/apply_action_fast`, but it is less deterministic.

Programmatic persistence is the better long-term path for mechanical edits if FuzzyCode can reliably identify and replace the `TouchpadControls.create({...})` object. This is a better fit for changes like image selection, role toggles, sizing, and explicit custom layout edits.

AI should remain useful for semantic detection when controls are missing or ambiguous. It should not be required for every mechanical config save.

## Ambiguity Resolution

AI should propose semantics. The library should enforce ergonomics. The user should resolve ambiguity visually.

Useful editor prompts/questions include:

- Use Player 1 controls?
- Move rare/super action to the utility area?
- This key looks like both jump and up. Treat it as a jump button?
- Pick images for punch, kick, special, or super?
- This game has too many buttons. Which actions are core?
- Keep this state-transition key as a utility button?

This avoids adding endless prompt-specific rules. The prompt can stay focused on detection, while the library and UI handle deterministic layout and user judgment.

## Principle

Do not make the prompt responsible for subjective layout taste or every edge case. Use the prompt to infer game controls and semantic action IDs. Use the library to make deterministic layout decisions. Use the editor UI when the right answer depends on user preference.
