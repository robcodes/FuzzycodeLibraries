# Touchpad Cases Log

Notes from manual testing of the top-voted outputs. These are tracked to guide future prompt and layout improvements.

## Gold standards (worked perfectly)
These are saved as regression configs in `test_cases/gold_standard_configs`.
- Asteroid Blaster with Boss Battles
- Bodysuit Jumper Platformer
- Bounce Quest to the Top
- Bubblebound
- Carrot Cruncher
- Dance Fever Boss Battle
- Fluffy Rope Swinger
- Googly Boomerang Quest
- Koala Survivor Rampage
- Simba’s Bug Adventure
- Space Invaders with Powerups
- Superhero Kid vs Ninja Animals
- Tetris Game

## Issues (investigate and improve)
- Cookie Monster Munch: Movement is direction-latched and cardinal. Keydown sets `nextDir` with no keyup handling, and movement continues on the grid without holding. From first principles: direction is a discrete selection (cardinal, mutually exclusive), and the thumb should choose one direction at a time. LLM should mark `activation: latch`, `direction_mode: cardinal`, and avoid `vector`/`simultaneous` so the library picks a digital D-pad.

## Special cases (record only for now)
- Bogglebeast Quest: Many keys; some weren’t detected. Improve extraction later.
- Bible Typerunner: Typing game; needs a full keyboard or input focus helper.
- Avoid the Germs (V3): Mouse-only; touch-to-mouse not yet supported.
- Cosmic Brick Blaster: Mouse-only; same as above.
- Frog Jumper Math Game: Already has solid tablet controls; we likely should detect and avoid injecting UI.
- Age of Empires style game: RTS complexity is too high for auto-touchpad; likely needs a different UX or skip.

## Notes (resolved or addressed)
- Bounce Quest: Rapid left/right drags sometimes stop moving until release. Fix applied: joystick now presses new directions in `move` events.
- Googly Boomerang Quest: `R` is restart only on game-over. A restart button shouldn’t take prime UI space during gameplay. Consider an `action_meta` field like `context: game_over` (or `importance: utility`) to hide/relocate it.

## Follow-ups
- Prompt: add guidance for “restart/pause only” actions to be marked as utility/contextual.
- Layout engine: add a digital D-pad layout driven by `action_meta` (move behavior = discrete).
- Idea: add a touch-to-mouse adapter for mouse-only games (virtual cursor or direct pointer mapping).
- Idea: add contextual/utility action placement (e.g., restart only on game-over).
- Idea: detect existing touch UI (onscreen controls) and suppress or reduce injected controls to avoid duplication.
