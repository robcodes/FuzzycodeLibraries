#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const DEFAULT_INPUT_DIR = "test_cases/outputs/top_voted";
const DEFAULT_LIST = "test_cases/gold_standard_good_list.txt";
const DEFAULT_OUTPUT_DIR = "test_cases/gold_standard_configs";

const parseArgs = () => {
    const args = process.argv.slice(2);
    let inputDir = DEFAULT_INPUT_DIR;
    let listPath = DEFAULT_LIST;
    let outputDir = DEFAULT_OUTPUT_DIR;
    for (let i = 0; i < args.length; i += 1) {
        const arg = args[i];
        if (arg === "--input-dir" && args[i + 1]) {
            inputDir = args[i + 1];
            i += 1;
        } else if (arg === "--list" && args[i + 1]) {
            listPath = args[i + 1];
            i += 1;
        } else if (arg === "--output-dir" && args[i + 1]) {
            outputDir = args[i + 1];
            i += 1;
        } else if (arg === "--help") {
            console.log("Usage: node scripts/export_gold_configs.js --input-dir <dir> --list <file> --output-dir <dir>");
            process.exit(0);
        }
    }
    return { inputDir, listPath, outputDir };
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

const loadList = (listPath, root) => {
    const resolved = path.resolve(root, listPath);
    if (!fs.existsSync(resolved)) {
        console.error(`List file not found: ${resolved}`);
        process.exit(1);
    }
    return fs.readFileSync(resolved, "utf8")
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line && !line.startsWith("#"));
};

const main = () => {
    const { inputDir, listPath, outputDir } = parseArgs();
    const root = path.join(__dirname, "..");
    const inputPath = path.resolve(root, inputDir);
    const outputPath = path.resolve(root, outputDir);

    if (!fs.existsSync(inputPath)) {
        console.error(`Input directory not found: ${inputPath}`);
        process.exit(1);
    }

    const names = loadList(listPath, root);
    if (!names.length) {
        console.error("No entries found in list file.");
        process.exit(1);
    }

    fs.mkdirSync(outputPath, { recursive: true });

    names.forEach((name) => {
        const fileName = name.endsWith(".html") ? name : `${name}_touch_embedded.html`;
        const filePath = path.join(inputPath, fileName);
        if (!fs.existsSync(filePath)) {
            console.warn(`Missing output HTML: ${filePath}`);
            return;
        }
        const content = fs.readFileSync(filePath, "utf8");
        const bindings = extractJson(content, "touchBindings");
        const actionMeta = extractJson(content, "touchActionMeta") || {};
        const layout = extractLayout(content);
        if (!bindings) {
            console.warn(`Skipping ${fileName}: missing touchBindings`);
            return;
        }

        const baseName = fileName.replace(/_touch_embedded\.html$/, "");
        const config = {
            layout,
            bindings,
            action_meta: actionMeta,
            source_output: path.relative(root, filePath)
        };
        const outPath = path.join(outputPath, `${baseName}_config.json`);
        fs.writeFileSync(outPath, JSON.stringify(config, null, 2));
        console.log(`Wrote: ${path.relative(root, outPath)}`);
    });
};

main();
