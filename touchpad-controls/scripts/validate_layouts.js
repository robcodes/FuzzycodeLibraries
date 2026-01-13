const path = require("path");
const TouchpadControls = require(path.join(__dirname, "..", "touchpad-controls.js"));

const layouts = [
    {
        name: "safe-platformer",
        bindings: {
            move: { left: "ArrowLeft", right: "ArrowRight" },
            primary: "Space",
            secondary: "KeyJ"
        }
    },
    {
        name: "fast-platformer",
        bindings: {
            move: { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" },
            primary: "Space",
            secondary: "KeyJ"
        }
    },
    {
        name: "dual-stick",
        bindings: {
            move: { left: "KeyA", right: "KeyD", up: "KeyW", down: "KeyS" },
            aim: { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" },
            primary: "Space"
        }
    },
    {
        name: "runner",
        bindings: {
            primary: "Space",
            secondary: "ArrowLeft",
            tertiary: "ArrowRight"
        }
    }
];

const viewports = [
    {
        name: "phone-portrait",
        width: 390,
        height: 844,
        safeArea: { top: 47, right: 0, bottom: 34, left: 0 }
    },
    {
        name: "phone-landscape",
        width: 844,
        height: 390,
        safeArea: { top: 0, right: 47, bottom: 21, left: 47 }
    },
    {
        name: "small-phone",
        width: 360,
        height: 640,
        safeArea: { top: 0, right: 0, bottom: 0, left: 0 }
    },
    {
        name: "tablet-portrait",
        width: 810,
        height: 1080,
        safeArea: { top: 24, right: 0, bottom: 20, left: 0 }
    },
    {
        name: "tablet-landscape",
        width: 1024,
        height: 768,
        safeArea: { top: 0, right: 0, bottom: 0, left: 0 }
    }
];

const failures = [];

const withinBounds = (button, metrics) => {
    const size = button.size || 0;
    const x = button.x;
    const y = button.y;
    const left = x - size / 2;
    const right = x + size / 2;
    const top = y - size / 2;
    const bottom = y + size / 2;
    const minX = metrics.safeArea.left + metrics.edgePadding;
    const maxX = metrics.width - metrics.safeArea.right - metrics.edgePadding;
    const minY = metrics.safeArea.top + metrics.edgePadding;
    const maxY = metrics.height - metrics.safeArea.bottom - metrics.edgePadding;

    if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(size)) {
        return "invalid position or size";
    }
    if (size < 48) {
        return `size ${size} below minimum target`;
    }
    if (left < minX || right > maxX || top < minY || bottom > maxY) {
        return `button exceeds bounds left=${left.toFixed(1)} right=${right.toFixed(1)} top=${top.toFixed(1)} bottom=${bottom.toFixed(1)}`;
    }
    return null;
};

for (const viewport of viewports) {
    for (const layout of layouts) {
        const result = TouchpadControls.buildLayout({
            layout: layout.name,
            bindings: layout.bindings,
            viewport: {
                width: viewport.width,
                height: viewport.height,
                safeArea: viewport.safeArea
            }
        });

        if (!result.buttons.length) {
            failures.push(`${viewport.name}/${layout.name}: no buttons created`);
            continue;
        }

        for (const button of result.buttons) {
            const error = withinBounds(button, result.metrics);
            if (error) {
                failures.push(`${viewport.name}/${layout.name}/${button.id || button.role}: ${error}`);
            }
        }
    }
}

if (failures.length) {
    console.error("Layout validation failures:\n" + failures.join("\n"));
    process.exit(1);
}

console.log("Layout validation passed for", viewports.length, "viewports and", layouts.length, "layouts.");
