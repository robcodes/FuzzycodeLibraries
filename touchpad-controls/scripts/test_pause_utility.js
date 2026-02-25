const assert = require("assert");
const { buildLayout } = require("../touchpad-controls.js");

const layout = buildLayout({
    layout: "auto",
    bindings: {
        move: { left: "KeyA", right: "KeyD", up: "KeyW", down: "KeyS" },
        primary: "KeyF",
        pause: "Escape"
    },
    actionMeta: {
        pause: { action_id: "pause-menu", behavior: "discrete", interaction: "tap", simultaneous: false }
    },
    viewport: { width: 1280, height: 720, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
});

const pause = layout.buttons.find((btn) => btn.role === "pause");
assert(pause, "pause utility button should be present when pause binding exists");
assert.strictEqual(pause.actionId, "pause-menu", "pause button should preserve action_id");
assert(pause.classList.includes("touchpad-utility-pause"), "pause should include utility class");
assert(
    pause.x > (layout.metrics.width * 0.75),
    "pause should be positioned on the right side near edge"
);
assert(pause.y < layout.metrics.height / 3, "pause should render near top");

console.log("Pause utility button test passed.");
