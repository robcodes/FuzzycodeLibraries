#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run touchpad injection over all test case games."
    )
    parser.add_argument(
        "--games-dir",
        default="test_cases/games",
        help="Directory containing source HTML test cases."
    )
    parser.add_argument(
        "--output-dir",
        default="test_cases/outputs",
        help="Directory for embedded output HTML files."
    )
    parser.add_argument(
        "--provider",
        default="groq",
        choices=["groq", "codex"],
        help="LLM provider to use."
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override for the selected provider."
    )
    parser.add_argument(
        "--reasoning-effort",
        default=None,
        help="Optional reasoning effort override."
    )
    parser.add_argument(
        "--prompt-template",
        default=None,
        help="Optional prompt template override."
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow empty bindings without failing."
    )
    parser.add_argument(
        "--debug-layout",
        action="store_true",
        help="Enable TouchpadControls debug layout logging."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the actions without running updates."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    games_dir = (root / args.games_dir).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(games_dir.glob("*.html"))
    if not html_files:
        print(f"No HTML files found in {games_dir}", file=sys.stderr)
        sys.exit(1)

    for html_path in html_files:
        output_path = output_dir / f"{html_path.stem}_touch_embedded.html"
        command = [
            sys.executable,
            str(root / "update_to_auto_touchpad_support.py"),
            "--game",
            str(html_path),
            "--embed-lib",
            "--output",
            str(output_path),
            "--provider",
            args.provider
        ]

        if args.model:
            command.extend(["--model", args.model])
        if args.reasoning_effort:
            command.extend(["--reasoning-effort", args.reasoning_effort])
        if args.prompt_template:
            command.extend(["--prompt-template", args.prompt_template])
        if args.allow_empty:
            command.append("--allow-empty")
        if args.debug_layout:
            command.append("--debug-layout")

        if args.dry_run:
            print("DRY RUN:", " ".join(command))
            continue

        print(f"Processing {html_path.name} -> {output_path.name}")
        result = subprocess.run(command, cwd=str(root))
        if result.returncode != 0:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
