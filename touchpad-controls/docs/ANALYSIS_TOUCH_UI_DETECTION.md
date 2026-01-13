# Existing Touch UI Detection: Where It Belongs

## Problem
Some games already ship with usable on-screen controls. Injecting an additional touchpad can
duplicate UI, block content, or confuse players.

## First-Principles Rationale
The library should be non-invasive and adaptive. When a page already provides functional touch
controls, the best default is to avoid interfering and preserve the original UI.

## Layering Proposal
### Update Script (Static Layer)
- Perform a lightweight HTML scan for obvious indicators:
  - class/id keywords like `touch`, `joystick`, `dpad`, `mobile-controls`
  - known joystick libraries or CSS patterns
- If detected, emit config flags like:
  - `auto_detect_touch_ui: true`
  - `prefer_existing_touch_ui: true`

This layer is conservative; it only hints to the runtime.

### Library (Runtime Layer)
Do the authoritative detection after load and on resize:
- Check for fixed-position controls near bottom corners.
- Look for elements with `touch-action` set and pointer/touch handlers.
- Detect known joystick markup (if present).

If detection is positive:
- Use `mode: "minimal"` (utility-only) or `suppress: true`.
- Allow user override to force our UI if desired.

## Determinism and Generalization
Detection is heuristic but deterministic once configured. It avoids genre-specific rules and
relies on common UI patterns that are broadly applicable across games.
