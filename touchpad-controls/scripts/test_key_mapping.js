const assert = require("assert");
const { resolveKeyDescriptor } = require("../touchpad-controls.js");

const cases = [
    { input: "KeyA", code: "KeyA", key: "a", keyCode: 65 },
    { input: "Digit9", code: "Digit9", key: "9", keyCode: 57 },
    { input: "ArrowLeft", code: "ArrowLeft", key: "ArrowLeft", keyCode: 37 },
    { input: "ArrowUp", code: "ArrowUp", key: "ArrowUp", keyCode: 38 },
    { input: "Space", code: "Space", key: " ", keyCode: 32 },
    { input: "Spacebar", code: "Space", key: " ", keyCode: 32 },
    { input: "Enter", code: "Enter", key: "Enter", keyCode: 13 },
    { input: "Esc", code: "Escape", key: "Escape", keyCode: 27 },
    { input: "ShiftLeft", code: "ShiftLeft", key: "Shift", keyCode: 16, location: 1 },
    { input: "ShiftRight", code: "ShiftRight", key: "Shift", keyCode: 16, location: 2 },
    { input: "Shift", code: "ShiftLeft", key: "Shift", keyCode: 16, location: 1 },
    { input: "ControlLeft", code: "ControlLeft", key: "Control", keyCode: 17, location: 1 },
    { input: "Control", code: "ControlLeft", key: "Control", keyCode: 17, location: 1 },
    { input: "AltRight", code: "AltRight", key: "Alt", keyCode: 18, location: 2 },
    { input: "Alt", code: "AltLeft", key: "Alt", keyCode: 18, location: 1 },
    { input: "MetaLeft", code: "MetaLeft", key: "Meta", keyCode: 91, location: 1 },
    { input: "Meta", code: "MetaLeft", key: "Meta", keyCode: 91, location: 1 },
    { input: "Backspace", code: "Backspace", key: "Backspace", keyCode: 8 },
    { input: "Delete", code: "Delete", key: "Delete", keyCode: 46 },
    { input: "Home", code: "Home", key: "Home", keyCode: 36 },
    { input: "PageUp", code: "PageUp", key: "PageUp", keyCode: 33 },
    { input: "F1", code: "F1", key: "F1", keyCode: 112 },
    { input: "F12", code: "F12", key: "F12", keyCode: 123 },
    { input: "Numpad0", code: "Numpad0", key: "0", keyCode: 96, location: 3 },
    { input: "Numpad9", code: "Numpad9", key: "9", keyCode: 105, location: 3 },
    { input: "NumpadAdd", code: "NumpadAdd", key: "+", keyCode: 107, location: 3 },
    { input: "NumpadEnter", code: "NumpadEnter", key: "Enter", keyCode: 13, location: 3 },
    { input: "Minus", code: "Minus", key: "-", keyCode: 189 },
    { input: "Equal", code: "Equal", key: "=", keyCode: 187 },
    { input: "BracketLeft", code: "BracketLeft", key: "[", keyCode: 219 },
    { input: "Backquote", code: "Backquote", key: "`", keyCode: 192 }
];

const failures = [];

cases.forEach((testCase) => {
    const result = resolveKeyDescriptor(testCase.input);
    ["code", "key", "keyCode", "location"].forEach((field) => {
        if (testCase[field] === undefined) return;
        if (result[field] !== testCase[field]) {
            failures.push({
                input: testCase.input,
                field,
                expected: testCase[field],
                got: result[field]
            });
        }
    });
});

if (failures.length) {
    failures.forEach((failure) => {
        console.error(
            `FAIL ${failure.input} ${failure.field}: expected ${failure.expected}, got ${failure.got}`
        );
    });
    process.exit(1);
}

console.log("All key mapping tests passed.");
