#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from pathlib import Path


ROLE_COLORS = {
    "move": "#1F6F8B",
    "aim": "#0F4C81",
    "primary": "#F59E0B",
    "secondary": "#60A5FA",
    "tertiary": "#A78BFA",
    "modifier": "#94A3B8",
    "jump": "#F97316",
    "magnitude": "#22C55E",
    "pause": "#64748B"
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render SVG (and optional PNG) snapshots from layout snapshot JSON."
    )
    parser.add_argument(
        "--input",
        default="test_cases/layout_snapshots/top_voted_layouts.json",
        help="Layout snapshot JSON file."
    )
    parser.add_argument(
        "--output-dir",
        default="test_cases/layout_renders",
        help="Directory to write SVG/PNG files."
    )
    parser.add_argument(
        "--list",
        default=None,
        help="Optional list of games to render (one per line)."
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Also render PNGs if an SVG converter is available."
    )
    return parser.parse_args()


def load_list(path: Path) -> set[str]:
    lines = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return set(lines)


def format_keys(keys) -> str:
    if keys is None:
        return ""
    if isinstance(keys, str):
        return keys
    if isinstance(keys, dict):
        parts = []
        for name in ("up", "down", "left", "right"):
            value = keys.get(name)
            if value:
                parts.append(f"{name}:{value}")
        return " ".join(parts)
    return str(keys)


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_svg(game_name: str, viewport_name: str, summary: dict, metrics: dict) -> str:
    width = metrics.get("width", 0)
    height = metrics.get("height", 0)
    safe_area = metrics.get("safeArea", {}) or {}
    safe_left = safe_area.get("left", 0)
    safe_right = safe_area.get("right", 0)
    safe_top = safe_area.get("top", 0)
    safe_bottom = safe_area.get("bottom", 0)

    safe_width = max(0, width - safe_left - safe_right)
    safe_height = max(0, height - safe_top - safe_bottom)

    layout_name = summary.get("layout", "auto")
    buttons = summary.get("buttons", []) or []

    header = f"{game_name} - {viewport_name} ({layout_name})"

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        "<style>",
        "text { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace; }",
        ".label { fill: #E2E8F0; font-size: 12px; }",
        ".title { fill: #E2E8F0; font-size: 14px; font-weight: 600; }",
        ".safe { fill: none; stroke: #475569; stroke-width: 2; stroke-dasharray: 6 4; }",
        ".button { stroke: #0F172A; stroke-width: 2; }",
        "</style>",
        "</defs>",
        f'<rect width="{width}" height="{height}" fill="#0B1020" />',
        f'<rect class="safe" x="{safe_left}" y="{safe_top}" width="{safe_width}" height="{safe_height}" />',
        f'<text class="title" x="12" y="22">{escape_xml(header)}</text>'
    ]

    for button in buttons:
        role = button.get("role") or "action"
        color = ROLE_COLORS.get(role, "#94A3B8")
        size = button.get("size", 0)
        radius = size / 2 if size else 0
        x = button.get("x", 0)
        y = button.get("y", 0)
        label = button.get("id") or role
        label_text = escape_xml(label)
        key_text = escape_xml(format_keys(button.get("keys")))
        font_size = max(10, min(14, int(radius / 2)))

        svg_parts.append(
            f'<g class="button-group">'
            f'<title>{label_text} {key_text}</title>'
            f'<circle class="button" cx="{x}" cy="{y}" r="{radius}" fill="{color}" />'
            f'<text class="label" x="{x}" y="{y + font_size / 3}" text-anchor="middle" font-size="{font_size}">{label_text}</text>'
            f'</g>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def write_png(svg_path: Path, png_path: Path) -> None:
    rsvg = shutil.which("rsvg-convert")
    inkscape = shutil.which("inkscape")
    magick = shutil.which("magick")
    convert = shutil.which("convert")

    if rsvg:
        subprocess.run([rsvg, "-o", str(png_path), str(svg_path)], check=False)
        return
    if inkscape:
        subprocess.run([inkscape, str(svg_path), "--export-type=png", "--export-filename", str(png_path)], check=False)
        return
    if magick:
        subprocess.run([magick, str(svg_path), str(png_path)], check=False)
        return
    if convert:
        subprocess.run([convert, str(svg_path), str(png_path)], check=False)
        return
    print("Warning: no SVG->PNG converter found; skipping PNG output.")


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    input_path = (root / args.input).resolve()
    output_dir = (root / args.output_dir).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {input_path}")

    allow = None
    if args.list:
        list_path = (root / args.list).resolve()
        allow = load_list(list_path)

    data = json.loads(input_path.read_text())
    games = data.get("games", {})

    for game_name, entry in sorted(games.items()):
        if allow and game_name not in allow:
            continue
        layouts = entry.get("layouts", {}) or {}
        for viewport_name, layout_entry in layouts.items():
            summary = layout_entry.get("summary") or {}
            metrics = layout_entry.get("metrics") or {}
            svg_text = build_svg(game_name, viewport_name, summary, metrics)
            out_dir = output_dir / game_name
            out_dir.mkdir(parents=True, exist_ok=True)
            svg_path = out_dir / f"{viewport_name}.svg"
            svg_path.write_text(svg_text)
            if args.png:
                png_path = out_dir / f"{viewport_name}.png"
                write_png(svg_path, png_path)

    print(f"Wrote layout renders to {output_dir}")


if __name__ == "__main__":
    main()
