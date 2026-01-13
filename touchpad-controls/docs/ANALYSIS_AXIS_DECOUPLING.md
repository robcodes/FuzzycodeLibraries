# Axis Decoupling: Rate vs Drive Controls

## Problem
Some games map left/right to a continuous rate change (orientation/heading) while mapping a
single direction to forward advance. When these are combined into one analog joystick, small
off-axis noise while pressing "forward" produces unintended rotation. This makes precise
straight input feel unstable even when the player intends a steady advance.

## First-Principles Rationale
This is not a genre issue; it is a control-space mismatch:
- Rate control changes heading (high sensitivity, bidirectional).
- Advance control changes magnitude (often low-granularity, sometimes unidirectional).
- A 2D analog stick encodes a single directional vector, so axes are inherently coupled.

If two axes belong to different control spaces (rate vs magnitude), coupling them produces
unwanted cross-axis effects and removes independent control. The correct response is to decouple
the axes into separate controls.
If the player must commonly hold two directions together with independent timing (hold one,
feather the other), those directions are not a single axis; they are separate degrees of freedom.

## LLM Output Semantics (Deterministic Bridge)
Ask the LLM to classify control space, not positions:
- `control_space: "vector"` for true 2D directional movement.
- `control_space: "rate"` for heading/orientation change (left/right).
- `control_space: "magnitude"` for advance/drive/accelerate (often a single direction).
- `simultaneous: true` when two directions are commonly held together during core play. If an
  axis would be `cardinal` but requires simultaneous holds, split into rate/magnitude axes.

The LLM does not decide layout; it only assigns roles.

## Deterministic Interpretation
Library should split controls when any of the following hold:
- The axis is asymmetric (e.g., only `up` present, no `down`) while left/right exist.
- `action_meta` indicates the vertical action is low-granularity while left/right are continuous.
- The LLM marks left/right as `control_space: "rate"` and the vertical action as `control_space: "magnitude"`.

## Layout Decision (Library-Owned)
- Render a horizontal-only control for the rate axis (two buttons or a slider).
- Render a separate advance/drive control (button or vertical slider if analog).
- Never allow diagonals between rate and magnitude in this mode.

## Why This Generalizes
This rule depends only on input topology and control semantics, not on genre labels. Any game
with a high-sensitivity rate axis and a low-granularity drive axis will benefit from decoupling,
regardless of theme.
