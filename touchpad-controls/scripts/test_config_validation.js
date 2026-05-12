const assert = require("assert");
const {
    buildLayout,
    validateConfig,
    TouchpadControlsConfigError
} = require("../touchpad-controls.js");

const validConfig = {
    layout: "auto",
    axes: [
        {
            usage: "movement",
            keys: { left: "KeyA", right: "KeyD", up: "KeyW", down: "KeyS" }
        }
    ],
    actions: {
        primary: { keys: "KeyF", action_id: "punch" },
        modifier: { keys: ["ShiftLeft", "KeyJ"], action_id: "super" }
    },
    viewport: { width: 800, height: 600, safeArea: { top: 0, right: 0, bottom: 0, left: 0 } }
};

const validResult = validateConfig(validConfig);
assert.strictEqual(validResult.ok, true, "valid config should pass validation");
assert.doesNotThrow(() => buildLayout(validConfig), "buildLayout should accept valid config");

const invalidConfig = {
    layout: "auto",
    actions: {
        primary: { keys: "KeyF, ShiftRight", action_id: "punch" }
    }
};

const invalidResult = validateConfig(invalidConfig);
assert.strictEqual(invalidResult.ok, false, "comma-separated key string should fail validation");
assert.strictEqual(invalidResult.errors[0].code, "INVALID_KEY_CODE_COMMA_LIST");
assert.strictEqual(invalidResult.errors[0].path, "actions.primary.keys");

assert.throws(
    () => buildLayout(invalidConfig),
    (err) => {
        assert(err instanceof TouchpadControlsConfigError);
        assert.strictEqual(err.code, "INVALID_KEY_CODE_COMMA_LIST");
        assert.strictEqual(err.details[0].path, "actions.primary.keys");
        assert(
            err.message.includes("Do not comma-separate alternate keys"),
            "error message should be understandable to the AI repair loop"
        );
        return true;
    },
    "buildLayout should throw a structured config error"
);

console.log("Config validation tests passed.");
