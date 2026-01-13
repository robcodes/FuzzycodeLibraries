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
        jump: { keys: "Space", behavior: "discrete", interaction: "tap", simultaneous: true }
    },
    viewport: { width: 800, height: 600, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
});

assert(result.bindings.move.left === "ArrowLeft", "analysis axes should map to bindings.move");
assert(result.bindings.jump === "Space", "analysis actions should map to bindings.jump");
assert(result.buttons.length > 0, "buttons should be generated from analysis input");

console.log("Analysis-input mapping test passed.");
