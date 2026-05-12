#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


VALID_CODE_RE = re.compile(
    r"^(?:"
    r"Key[A-Z]|Digit[0-9]|"
    r"Arrow(?:Left|Right|Up|Down)|"
    r"Space|Enter|Tab|Escape|Backspace|Delete|Insert|Home|End|PageUp|PageDown|"
    r"CapsLock|NumLock|ScrollLock|Pause|PrintScreen|ContextMenu|"
    r"Shift(?:Left|Right)|Control(?:Left|Right)|Alt(?:Left|Right)|Meta(?:Left|Right)|"
    r"Minus|Equal|BracketLeft|BracketRight|Backslash|Semicolon|Quote|Backquote|Comma|Period|Slash|"
    r"F(?:[1-9]|1[0-2])|"
    r"Numpad(?:[0-9]|Add|Subtract|Multiply|Divide|Decimal|Enter|Equal)"
    r")$"
)

KEY_FIELD_NAMES = {"keys", "key", "code", "codes"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate TouchpadControls configs for runtime-usable key codes."
    )
    parser.add_argument("paths", nargs="+", help="JSON or embedded HTML files to validate.")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow configs with no axes/actions/bindings."
    )
    return parser.parse_args()


def extract_const_json(content: str, name: str) -> Any:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*([\s\S]*?);", content)
    if not match:
        return None
    return json.loads(match.group(1))


def extract_balanced_object(source: str, call_name: str) -> str | None:
    call_index = source.find(call_name)
    if call_index < 0:
        return None
    start = source.find("{", call_index)
    if start < 0:
        return None

    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'", "`"}:
            quote = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    return None


def extract_js_touchpad_key_values(config_source: str) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []

    # keys: "KeyF" / key: "KeyF" / code: "KeyF"
    scalar_pattern = re.compile(
        r"\b(keys|key|code)\s*:\s*(['\"])(.*?)\2",
        re.DOTALL,
    )
    for match in scalar_pattern.finditer(config_source):
        values.append((f"TouchpadControls.create.{match.group(1)}", match.group(3)))

    # keys: ["KeyF", "ShiftRight"]
    array_pattern = re.compile(r"\b(keys|codes)\s*:\s*\[([\s\S]*?)\]")
    string_pattern = re.compile(r"(['\"])(.*?)\1", re.DOTALL)
    for match in array_pattern.finditer(config_source):
        for index, item in enumerate(string_pattern.finditer(match.group(2))):
            values.append((f"TouchpadControls.create.{match.group(1)}[{index}]", item.group(2)))

    # keys: { left: "KeyA", right: "KeyD", ... }
    direction_pattern = re.compile(
        r"\b(left|right|up|down)\s*:\s*(['\"])(.*?)\2",
        re.DOTALL,
    )
    for match in direction_pattern.finditer(config_source):
        values.append((f"TouchpadControls.create.keys.{match.group(1)}", match.group(3)))

    return values


def load_config(path: Path) -> Any:
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".html", ".htm"}:
        bindings = extract_const_json(content, "touchBindings")
        action_meta = extract_const_json(content, "touchActionMeta") or {}
        if bindings is not None:
            return {"bindings": bindings, "action_meta": action_meta}

        inline_json = re.search(
            r'<script[^>]+id=["\']touchpad-bindings-json["\'][^>]*>([\s\S]*?)</script>',
            content,
            re.IGNORECASE,
        )
        if inline_json:
            return json.loads(inline_json.group(1))

        create_source = extract_balanced_object(content, "TouchpadControls.create")
        if create_source:
            raw_key_values = extract_js_touchpad_key_values(create_source)
            if raw_key_values:
                return {"__raw_key_values__": raw_key_values}

        raise ValueError("embedded HTML does not contain touchBindings JSON")

    return json.loads(content)


def key_paths(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    hits: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in KEY_FIELD_NAMES:
                hits.append((child_path, child))
            else:
                hits.extend(key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(key_paths(child, f"{path}[{index}]"))
    return hits


def flatten_key_values(value: Any, path: str) -> list[tuple[str, Any]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        out: list[tuple[str, Any]] = []
        for index, item in enumerate(value):
            out.extend(flatten_key_values(item, f"{path}[{index}]"))
        return out
    if isinstance(value, dict):
        out: list[tuple[str, Any]] = []
        for key, item in value.items():
            out.extend(flatten_key_values(item, f"{path}.{key}"))
        return out
    return [(path, value)]


def config_has_controls(config: Any) -> bool:
    if not isinstance(config, dict):
        return False
    if config.get("__raw_key_values__"):
        return True
    axes = config.get("axes")
    actions = config.get("actions")
    bindings = config.get("bindings")
    return (
        isinstance(axes, list) and bool(axes)
        or isinstance(actions, dict) and bool(actions)
        or isinstance(bindings, dict) and bool(bindings)
    )


def validate_key_string(value: str) -> str | None:
    if value != value.strip():
        return "has leading/trailing whitespace"
    if "," in value:
        return "contains a comma; use one key code string or an array of key code strings"
    if re.search(r"\s", value):
        return "contains whitespace; use KeyboardEvent.code values such as KeyF or ShiftRight"
    if "+" in value:
        return "contains '+'; use an array for simultaneous key presses"
    if not VALID_CODE_RE.match(value):
        return "is not a recognized KeyboardEvent.code value"
    return None


def validate_config(config: Any, *, allow_empty: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return ["config root must be an object"]

    if not allow_empty and not config_has_controls(config):
        errors.append("config has no axes/actions/bindings")

    raw_key_values = config.get("__raw_key_values__")
    if isinstance(raw_key_values, list):
        for item in raw_key_values:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            value_path, value = item
            if not isinstance(value, str):
                errors.append(f"{value_path}: key value must be a string, got {type(value).__name__}")
                continue
            reason = validate_key_string(value)
            if reason:
                errors.append(f"{value_path}: {value!r} {reason}")
        return errors

    for key_path, raw_value in key_paths(config):
        for value_path, value in flatten_key_values(raw_value, key_path):
            if not isinstance(value, str):
                errors.append(f"{value_path}: key value must be a string, got {type(value).__name__}")
                continue
            reason = validate_key_string(value)
            if reason:
                errors.append(f"{value_path}: {value!r} {reason}")

    return errors


def main() -> int:
    args = parse_args()
    had_error = False

    for raw_path in args.paths:
        path = Path(raw_path)
        try:
            config = load_config(path)
            errors = validate_config(config, allow_empty=args.allow_empty)
        except Exception as exc:
            errors = [str(exc)]

        if errors:
            had_error = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
