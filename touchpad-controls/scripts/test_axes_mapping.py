#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from update_to_auto_touchpad_support import extract_bindings_from_axes_actions  # noqa: E402


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_movement_and_aim():
    data = {
        "axes": [
            {
                "usage": "movement",
                "priority": "primary",
                "control_space": "vector",
                "keys": {"left": "KeyA", "right": "KeyD"}
            },
            {
                "usage": "aim",
                "priority": "primary",
                "control_space": "vector",
                "keys": {"left": "ArrowLeft", "right": "ArrowRight"}
            }
        ],
        "actions": {}
    }
    bindings, meta = extract_bindings_from_axes_actions(data)
    check(bindings["move"]["left"] == "KeyA", "movement axis should map to move")
    check(bindings["aim"]["left"] == "ArrowLeft", "aim axis should map to aim")


def test_single_aim_becomes_move():
    data = {
        "axes": [
            {
                "usage": "aim",
                "priority": "primary",
                "control_space": "rate",
                "keys": {"left": "ArrowLeft", "right": "ArrowRight"}
            }
        ],
        "actions": {}
    }
    bindings, meta = extract_bindings_from_axes_actions(data)
    check("move" in bindings, "single aim axis should map to move")
    check("aim" not in bindings, "single aim axis should not create aim binding")


def test_primary_secondary_aim():
    data = {
        "axes": [
            {
                "usage": "aim",
                "priority": "secondary",
                "control_space": "vector",
                "keys": {"left": "KeyJ", "right": "KeyL"}
            },
            {
                "usage": "aim",
                "priority": "primary",
                "control_space": "rate",
                "keys": {"left": "ArrowLeft", "right": "ArrowRight"}
            }
        ],
        "actions": {}
    }
    bindings, meta = extract_bindings_from_axes_actions(data)
    check(bindings["move"]["left"] == "ArrowLeft", "primary aim axis should map to move")
    check(bindings["aim"]["left"] == "KeyJ", "secondary aim axis should map to aim")


def test_magnitude_action():
    data = {
        "axes": [
            {
                "usage": "movement",
                "priority": "primary",
                "control_space": "magnitude",
                "keys": {"up": "ArrowUp"}
            }
        ],
        "actions": {}
    }
    bindings, meta = extract_bindings_from_axes_actions(data)
    check(bindings["magnitude"] == "ArrowUp", "magnitude axis should map to magnitude action")
    check("move" not in bindings, "magnitude axis should not create move binding")


def test_activation_direction_mode():
    data = {
        "axes": [
            {
                "usage": "movement",
                "priority": "primary",
                "control_space": "vector",
                "activation": "latch",
                "direction_mode": "cardinal",
                "keys": {"left": "ArrowLeft", "right": "ArrowRight"}
            }
        ],
        "actions": {}
    }
    bindings, meta = extract_bindings_from_axes_actions(data)
    check(meta["move"]["activation"] == "latch", "activation should be preserved")
    check(meta["move"]["direction_mode"] == "cardinal", "direction_mode should be preserved")


def test_granularity_preserved():
    data = {
        "axes": [
            {
                "usage": "movement",
                "priority": "primary",
                "control_space": "vector",
                "granularity": "coarse",
                "keys": {"left": "ArrowLeft", "right": "ArrowRight"}
            }
        ],
        "actions": {}
    }
    bindings, meta = extract_bindings_from_axes_actions(data)
    check(meta["move"]["granularity"] == "coarse", "granularity should be preserved")


def test_simultaneous_preserved():
    data = {
        "axes": [
            {
                "usage": "movement",
                "priority": "primary",
                "control_space": "vector",
                "simultaneous": True,
                "keys": {"left": "ArrowLeft", "right": "ArrowRight"}
            }
        ],
        "actions": {}
    }
    bindings, meta = extract_bindings_from_axes_actions(data)
    check(meta["move"]["simultaneous"] is True, "simultaneous should be preserved")


def main():
    test_movement_and_aim()
    test_single_aim_becomes_move()
    test_primary_secondary_aim()
    test_magnitude_action()
    test_activation_direction_mode()
    test_granularity_preserved()
    test_simultaneous_preserved()
    print("All axes mapping tests passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
