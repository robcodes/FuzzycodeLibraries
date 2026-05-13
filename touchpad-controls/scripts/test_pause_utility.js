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

const overflowLayout = buildLayout({
    layout: "auto",
    bindings: {
        move: { left: "KeyA", right: "KeyD" },
        jump: "KeyW",
        primary: "KeyF",
        secondary: "KeyG",
        tertiary: "KeyH",
        modifier: "KeyJ"
    },
    actionMeta: {
        jump: { action_id: "jump", behavior: "discrete", interaction: "tap", simultaneous: true },
        primary: { action_id: "punch", behavior: "discrete", interaction: "tap", simultaneous: true },
        secondary: { action_id: "kick", behavior: "discrete", interaction: "tap", simultaneous: true },
        tertiary: { action_id: "special", behavior: "discrete", interaction: "tap", simultaneous: true },
        modifier: { action_id: "super", behavior: "discrete", interaction: "tap", simultaneous: true }
    },
    viewport: { width: 1280, height: 720, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
});

const superButton = overflowLayout.buttons.find((btn) => btn.actionId === "super");
assert(superButton, "rare overflow action should still render");
assert.strictEqual(superButton.role, "modifier", "super should preserve its original role");
assert(superButton.classList.includes("touchpad-utility-overflow"), "super should move to utility overflow strip");
assert(superButton.y < overflowLayout.metrics.height / 3, "super should render near top");
assert(!overflowLayout.warnings.length, "rendered overflow action should not produce a warning");

console.log("Pause utility button test passed.");
