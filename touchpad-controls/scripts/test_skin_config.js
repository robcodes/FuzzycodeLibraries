const assert = require("assert");
const TouchpadControls = require("../touchpad-controls.js");

const { normalizeSkin, resolveSkinThemeForButton } = TouchpadControls._internal;

const skin = normalizeSkin({
    hideDefaultIcons: true,
    joystick: {
        baseImage: "https://images.example/base.png",
        knobImage: "https://images.example/knob.png"
    },
    buttonFallback: {
        background: "rgba(0,0,0,0.55)",
        border: "1px solid rgba(255,255,255,0.35)"
    },
    roles: {
        primary: { image: "https://images.example/primary.png", foregroundSize: "82%" },
        secondary: "https://images.example/secondary.png"
    },
    actions: {
        kick: { image: "https://images.example/kick.png" }
    }
});

assert(skin, "skin should normalize");
assert.strictEqual(skin.hideDefaultIcons, true, "hideDefaultIcons should be preserved");
assert.strictEqual(skin.joystick.baseImage, "https://images.example/base.png");
assert.strictEqual(skin.joystick.knobImage, "https://images.example/knob.png");
assert.strictEqual(skin.roles.primary.foregroundImage, "https://images.example/primary.png");
assert.strictEqual(skin.roles.secondary.foregroundImage, "https://images.example/secondary.png");
assert.strictEqual(skin.actions.kick.foregroundImage, "https://images.example/kick.png");

const primaryTheme = resolveSkinThemeForButton(
    skin,
    { role: "primary" },
    "button"
);
assert(primaryTheme, "primary theme should resolve");
assert.strictEqual(primaryTheme.iconOpacity, 0, "skin should hide default icons");
assert.strictEqual(primaryTheme.background, "rgba(0,0,0,0.55)");
assert.strictEqual(primaryTheme.border, "1px solid rgba(255,255,255,0.35)");
assert.strictEqual(primaryTheme.foregroundImage, "https://images.example/primary.png");
assert.strictEqual(primaryTheme.foregroundSize, "82%");

const joystickTheme = resolveSkinThemeForButton(
    skin,
    { role: "move" },
    "joystick"
);
assert(joystickTheme, "joystick theme should resolve");
assert.strictEqual(joystickTheme.iconOpacity, 0, "hideDefaultIcons should affect joystick too");
assert.strictEqual(
    joystickTheme.background,
    undefined,
    "button fallback should not be applied to joystick controls"
);

const actionTheme = resolveSkinThemeForButton(
    skin,
    { role: "secondary", actionId: "kick" },
    "button"
);
assert.strictEqual(actionTheme.foregroundImage, "https://images.example/kick.png");

console.log("Skin configuration tests passed.");
