#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


MARKER = "root.TouchpadControls = factory();"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update embedded touchpad-controls.js inside HTML outputs."
    )
    parser.add_argument(
        "--dir",
        default="test_cases/outputs/top_voted",
        help="Directory containing embedded output HTML files."
    )
    parser.add_argument(
        "--pattern",
        default="*_touch_embedded.html",
        help="Glob pattern to match HTML files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing files."
    )
    return parser.parse_args()


def escape_script(content: str) -> str:
    return content.replace("</script", "<\\/script")


def update_file(path: Path, replacement: str) -> bool:
    text = path.read_text()
    script_pattern = re.compile(r"<script>([\s\S]*?)</script>")
    matches = list(script_pattern.finditer(text))
    if not matches:
        return False
    updated = False
    for match in matches:
        if MARKER not in match.group(1):
            continue
        start, end = match.span(1)
        text = text[:start] + "\n" + replacement + "\n" + text[end:]
        updated = True
        break
    if updated:
        path.write_text(text)
    return updated


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    target_dir = (root / args.dir).resolve()
    if not target_dir.exists():
        raise FileNotFoundError(f"Directory not found: {target_dir}")

    lib_path = root / "touchpad-controls.js"
    if not lib_path.exists():
        raise FileNotFoundError(f"touchpad-controls.js not found at {lib_path}")

    replacement = escape_script(lib_path.read_text())
    files = sorted(target_dir.glob(args.pattern))
    if not files:
        raise FileNotFoundError(f"No files matched {args.pattern} in {target_dir}")

    updated_files = []
    skipped_files = []
    for file_path in files:
        try:
            if args.dry_run:
                text = file_path.read_text()
                if MARKER in text:
                    updated_files.append(file_path)
                else:
                    skipped_files.append(file_path)
                continue
            changed = update_file(file_path, replacement)
            if changed:
                updated_files.append(file_path)
            else:
                skipped_files.append(file_path)
        except Exception:
            skipped_files.append(file_path)

    print(f"Updated {len(updated_files)} file(s).")
    if skipped_files:
        print(f"Skipped {len(skipped_files)} file(s) (marker not found).")


if __name__ == "__main__":
    main()
