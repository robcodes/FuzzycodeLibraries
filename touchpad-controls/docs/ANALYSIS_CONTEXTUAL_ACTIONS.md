# Contextual / Utility Actions: Deterministic Handling

## Problem
Some actions (restart, menu, pause) are only relevant in specific game states. If they are
placed in primary control space, they consume valuable reachability for actions that must be
used during active play.

## First-Principles Rationale
UI real estate on touch screens is limited. Actions that are:
- infrequent,
- not simultaneous with movement,
- or only used in specific states
should not compete with primary actions for thumb space. This is a universal ergonomics rule,
independent of genre.

## LLM Output Semantics (Deterministic Bridge)
Ask the LLM to classify each action with two small enums:
- `importance`: `primary | secondary | utility`
- `context`: `always | game_over | menu | debug`

These labels are compact and universal. The LLM does not decide placement.

## Deterministic Interpretation (Update Script)
- Validate the enums strictly; drop unknown values.
- If the LLM does not supply `context`, default to `always`.
- If the LLM does not supply `importance`, default to `secondary`.
- Only apply special placement rules when `importance: utility` is explicitly provided.

## Layout Decision (Library-Owned)
Deterministic rules:
- `utility` actions go to a small top strip or corner cluster (reduced size).
- Non-`always` contexts are hidden by default.
- Provide a single method to reveal a context: `TouchpadControls.setContext("game_over")`.

## Why This Generalizes
The scheme encodes action criticality and state-dependence without genre assumptions. It relies
on a small deterministic schema and keeps placement entirely in the library.
