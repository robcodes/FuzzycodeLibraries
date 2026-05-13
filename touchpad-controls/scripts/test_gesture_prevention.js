const assert = require("assert");
const { _internal } = require("../touchpad-controls.js");

const originalDocument = global.document;

function makeElement(tagName, parent = null) {
    return {
        nodeType: 1,
        tagName,
        parentElement: parent,
        parentNode: parent,
        onclick: null,
        isContentEditable: false,
        attributes: new Map(),
        getAttribute(name) {
            return this.attributes.get(name) || null;
        },
        hasAttribute(name) {
            return this.attributes.has(name);
        },
        closest(selector) {
            if (selector === ".excluded" && this.attributes.get("class") === "excluded") {
                return this;
            }
            return parent && typeof parent.closest === "function" ? parent.closest(selector) : null;
        }
    };
}

const listeners = {};
global.document = {
    nodeType: 9,
    addEventListener(type, handler) {
        listeners[type] = handler;
    },
    removeEventListener(type, handler) {
        if (listeners[type] === handler) delete listeners[type];
    }
};

try {
    const clickableCard = makeElement("DIV");
    clickableCard.onclick = () => {};
    const cardCanvas = makeElement("CANVAS", clickableCard);
    const plainCanvas = makeElement("CANVAS");

    assert.strictEqual(
        _internal.isDefaultInteractiveTarget(cardCanvas),
        true,
        "children of custom onclick controls should be treated as interactive"
    );
    assert.strictEqual(
        _internal.isDefaultInteractiveTarget(plainCanvas),
        false,
        "plain canvas should still allow gesture prevention"
    );

    const remove = _internal.createGesturePrevention();
    assert.strictEqual(typeof listeners.touchstart, "function", "touchstart handler should be registered");

    let clickablePrevented = false;
    listeners.touchstart({
        target: cardCanvas,
        preventDefault() {
            clickablePrevented = true;
        }
    });
    assert.strictEqual(clickablePrevented, false, "clickable custom UI should keep native tap/click behavior");

    let canvasPrevented = false;
    listeners.touchstart({
        target: plainCanvas,
        preventDefault() {
            canvasPrevented = true;
        }
    });
    assert.strictEqual(canvasPrevented, true, "plain game surface should still prevent default gestures");

    remove();
    assert.strictEqual(listeners.touchstart, undefined, "gesture prevention cleanup should remove handlers");
} finally {
    global.document = originalDocument;
}

console.log("Gesture prevention tests passed.");
