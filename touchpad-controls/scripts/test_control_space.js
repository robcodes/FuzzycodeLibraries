const assert = require("assert");
const { buildLayout } = require("../touchpad-controls.js");

const layout = buildLayout({
    layout: "auto",
    bindings: {
        move: { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp" },
        primary: "ArrowUp"
    },
    actionMeta: {
        move: { kind: "axis", control_space: "rate", behavior: "continuous", interaction: "hold", simultaneous: true },
        primary: {
            kind: "button",
            control_space: "magnitude",
            behavior: "continuous",
            interaction: "hold",
            simultaneous: true
        }
    },
    viewport: { width: 800, height: 600, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
});

assert.strictEqual(layout.layout, "safe-platformer");
assert.strictEqual(layout.actionMeta.move.control_space, "rate");

const move = layout.buttons.find((btn) => btn.role === "move");
assert(move, "move button missing");
assert(move.keys.left && move.keys.right, "move should keep left/right");
assert(!move.keys.up && !move.keys.down, "move should drop vertical when control_space=rate");

const primary = layout.buttons.find((btn) => btn.role === "primary");
assert(primary, "primary button missing");

console.log("All control_space tests passed.");
