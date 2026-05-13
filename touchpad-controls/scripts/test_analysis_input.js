const assert = require("assert");
const { buildLayout } = require("../touchpad-controls.js");

const result = buildLayout({
    layout: "auto",
    axes: [
        {
            usage: "movement",
            priority: "primary",
            control_space: "vector",
            keys: { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" },
            behavior: "continuous",
            interaction: "hold",
            activation: "hold",
            direction_mode: "vector",
            granularity: "fine",
            simultaneous: true
        }
    ],
    actions: {
        jump: { keys: "Space", action_id: "jump", behavior: "discrete", interaction: "tap", simultaneous: true }
    },
    viewport: { width: 800, height: 600, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
});

assert(result.bindings.move.left === "ArrowLeft", "analysis axes should map to bindings.move");
assert(result.bindings.jump === "Space", "analysis actions should map to bindings.jump");
assert(result.actionMeta.jump.action_id === "jump", "analysis action_id should map to actionMeta");
assert(result.buttons.length > 0, "buttons should be generated from analysis input");
const jumpButton = result.buttons.find((btn) => btn.role === "jump");
assert(jumpButton && jumpButton.actionId === "jump", "jump action_id should map to rendered button");

const duplicateResult = buildLayout({
    layout: "auto",
    axes: [
        {
            usage: "movement",
            priority: "primary",
            control_space: "vector",
            keys: { left: "KeyA", right: "KeyD", up: "KeyW", down: "KeyS" },
            behavior: "continuous",
            interaction: "hold",
            activation: "hold",
            direction_mode: "vector",
            granularity: "fine",
            simultaneous: true
        }
    ],
    actions: {
        jump: { keys: "KeyW", action_id: "jump", behavior: "discrete", interaction: "tap", simultaneous: true }
    },
    viewport: { width: 800, height: 600, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
});

assert.strictEqual(duplicateResult.bindings.move.up, null, "discrete duplicate jump key should be removed from movement up");
assert.strictEqual(duplicateResult.bindings.jump, "KeyW", "duplicate key should remain as jump action");
assert.strictEqual(duplicateResult.layout, "fast-platformer", "remaining down key should still require vertical movement");
assert(
    duplicateResult.warnings.some((warning) => warning.code === "DUPLICATE_AXIS_ACTION_KEY_RESOLVED"),
    "duplicate axis/action key should produce a warning"
);

const horizontalDuplicateResult = buildLayout({
    layout: "auto",
    axes: [
        {
            usage: "movement",
            priority: "primary",
            control_space: "vector",
            keys: { left: "KeyA", right: "KeyD", up: "KeyW" },
            behavior: "continuous",
            interaction: "hold",
            activation: "hold",
            direction_mode: "vector",
            granularity: "fine",
            simultaneous: true
        }
    ],
    actions: {
        jump: { keys: "KeyW", action_id: "jump", behavior: "discrete", interaction: "tap", simultaneous: true }
    },
    viewport: { width: 800, height: 600, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
});

assert.strictEqual(horizontalDuplicateResult.bindings.move.up, null, "jump should not stay on the axis");
assert.strictEqual(horizontalDuplicateResult.layout, "safe-platformer", "axis should collapse to horizontal movement when only jump was vertical");

console.log("Analysis-input mapping test passed.");
