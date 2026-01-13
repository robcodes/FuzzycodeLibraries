#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const TouchpadControls = require(path.join(__dirname, "..", "touchpad-controls.js"));

const DEFAULT_INPUT_DIR = "test_cases/outputs/top_voted";
const DEFAULT_OUTPUT = "test_cases/layout_snapshots/top_voted_layouts.json";
const DEFAULT_LIST = null;

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

const parseArgs = () => {
    const args = process.argv.slice(2);
    let inputDir = DEFAULT_INPUT_DIR;
    let output = DEFAULT_OUTPUT;
    let listPath = DEFAULT_LIST;
    for (let i = 0; i < args.length; i += 1) {
        const arg = args[i];
        if (arg === "--input-dir" && args[i + 1]) {
            inputDir = args[i + 1];
            i += 1;
        } else if (arg === "--output" && args[i + 1]) {
            output = args[i + 1];
            i += 1;
        } else if (arg === "--list" && args[i + 1]) {
            listPath = args[i + 1];
            i += 1;
        } else if (arg === "--help") {
            console.log("Usage: node scripts/export_layout_snapshots.js --input-dir <dir> --output <file> --list <file>");
            process.exit(0);
        }
    }
    return { inputDir, output, listPath };
};

const extractJson = (content, name) => {
    const regex = new RegExp(`const\\s+${name}\\s*=\\s*([\\s\\S]*?);`);
    const match = content.match(regex);
    if (!match) return null;
    return JSON.parse(match[1]);
};

const extractLayout = (content) => {
    const match = content.match(/layout:\\s*\"([^\"]+)\"/);
    return match ? match[1] : "auto";
};

const roundValue = (value) => {
    if (typeof value !== "number" || !Number.isFinite(value)) return value;
    return Math.round(value * 10) / 10;
};

const roundDeep = (value) => {
    if (Array.isArray(value)) return value.map(roundDeep);
    if (value && typeof value === "object") {
        const out = {};
        Object.entries(value).forEach(([key, val]) => {
            out[key] = roundDeep(val);
        });
        return out;
    }
    return roundValue(value);
};

const summarizeLayout = (layoutConfig) => {
    if (TouchpadControls._internal && typeof TouchpadControls._internal.summarizeLayout === "function") {
        return TouchpadControls._internal.summarizeLayout(layoutConfig);
    }
    const buttons = Array.isArray(layoutConfig.buttons) ? layoutConfig.buttons : [];
    return {
        layout: layoutConfig.layout || null,
        buttons: buttons.map((btn) => ({
            id: btn.id || null,
            role: btn.role || null,
            type: btn.type || (btn.keys && typeof btn.keys === "object" ? "joystick" : "button"),
            keys: btn.keys || null,
            x: roundValue(btn.x),
            y: roundValue(btn.y),
            size: roundValue(btn.size)
        }))
    };
};

const main = () => {
    const { inputDir, output, listPath } = parseArgs();
    const root = path.join(__dirname, "..");
    const inputPath = path.resolve(root, inputDir);
    const outputPath = path.resolve(root, output);

    if (!fs.existsSync(inputPath)) {
        console.error(`Input directory not found: ${inputPath}`);
        process.exit(1);
    }

    const files = fs.readdirSync(inputPath)
        .filter((name) => name.endsWith(".html"))
        .sort();

    if (!files.length) {
        console.error(`No HTML files found in ${inputPath}`);
        process.exit(1);
    }

    const results = {
        generated_at: new Date().toISOString(),
        source_dir: path.relative(root, inputPath),
        viewports: viewports.map((vp) => ({
            name: vp.name,
            width: vp.width,
            height: vp.height,
            safeArea: vp.safeArea
        })),
        games: {}
    };

    let allowed = null;
    if (listPath) {
        const resolvedList = path.resolve(root, listPath);
        if (!fs.existsSync(resolvedList)) {
            console.error(`List file not found: ${resolvedList}`);
            process.exit(1);
        }
        const lines = fs.readFileSync(resolvedList, "utf8")
            .split(/\r?\n/)
            .map((line) => line.trim())
            .filter((line) => line && !line.startsWith("#"));
        allowed = new Set(lines);
    }

    files.forEach((file) => {
        const baseName = file.replace(/_touch_embedded\.html$/, "");
        if (allowed) {
            if (!allowed.has(baseName) && !allowed.has(file)) {
                return;
            }
        }
        const filePath = path.join(inputPath, file);
        const content = fs.readFileSync(filePath, "utf8");
        const bindings = extractJson(content, "touchBindings");
        const actionMeta = extractJson(content, "touchActionMeta") || {};
        const layout = extractLayout(content);
        if (!bindings) {
            console.warn(`Skipping ${file}: missing touchBindings`);
            return;
        }

        const entry = {
            file: path.relative(root, filePath),
            layout,
            bindings,
            actionMeta,
            layouts: {}
        };

        viewports.forEach((vp) => {
            const layoutConfig = TouchpadControls.buildLayout({
                layout,
                bindings,
                actionMeta,
                viewport: {
                    width: vp.width,
                    height: vp.height,
                    safeArea: vp.safeArea
                }
            });
            entry.layouts[vp.name] = {
                summary: summarizeLayout(layoutConfig),
                metrics: roundDeep(layoutConfig.metrics)
            };
        });

        results.games[baseName] = entry;
    });

    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
    console.log(`Wrote layout snapshots: ${path.relative(root, outputPath)}`);
};

main();
