# Layering Logic (First-Principles)

This document explains what logic belongs in each layer, why it belongs there, and how the
nondeterministic LLM output is bridged into deterministic behavior.

## Layers
1) **LLM extraction (nondeterministic)**
2) **Update script (deterministic normalization)**
3) **Library (deterministic layout + input)**
4) **Runtime detection (deterministic heuristics)**
5) **Manual overrides / product integration**

## First-Principles Criteria
- **Determinism**: layout decisions must be repeatable and testable.
- **Semantics vs ergonomics**: the LLM should infer semantics; the library should handle ergonomics.
- **Runtime knowledge**: anything requiring DOM/viewport state belongs at runtime.
- **Conservatism**: heuristic inference should only happen where it is safe and reversible.

## What Belongs Where (and Why)

### 1) LLM extraction (semantics only)
**Responsibilities**
- Extract keyboard controls (`bindings`) from HTML/JS.
- Label universal semantics (`action_meta`):
  - `kind`, `behavior`, `interaction`, `simultaneous`
  - `control_space`: `vector`, `rate`, `magnitude`
  - `importance`, `context` (future)
 - Follow the canonical schema and rules in `prompts/pipeline_prompt_template.md` (manual prompts must mirror it).

**Why here**
- The LLM can interpret code intent and usage patterns that are hard to encode deterministically.
- It should not decide positions or sizes; that would introduce non-repeatable layout choices.

**Principle**
LLM outputs **only** semantics, never layout.

### 2) Update script (schema normalization)
**Responsibilities**
- Validate and sanitize the LLM output into strict enums.
- Apply conservative, deterministic fallbacks:
  - `detect_discrete_move` if movement appears keydown-only.
- Persist inputs/outputs for audit (`llm_runs/run_###`).

**Why here**
- This layer is deterministic and repeatable.
- It is the bridge from nondeterministic text to deterministic config.

**Principle**
If a heuristic is used here, it must be:
- explicit,
- low-risk,
- and reversible (library can still override with user config).

### 3) Library (layout + ergonomics)
**Responsibilities**
- Choose layout archetype from semantics (`control_space`, `behavior`, `axes`).
- Compute positions, sizes, and spacing from viewport metrics.
- Emit keyboard events predictably.

**Why here**
- The library is deterministic and testable.
- It owns ergonomics so the LLM never has to.

**Principle**
The library is the single source of truth for layout behavior.

### 4) Runtime detection (DOM-aware heuristics)
**Responsibilities**
- Detect existing on-screen touch UI.
- Apply safe-area, orientation, and viewport changes.

**Why here**
- Only runtime has actual DOM/layout context.
- Static analysis cannot reliably detect UI presence or safe areas.

**Principle**
DOM-aware heuristics must live in the runtime layer, not in the LLM prompt.

### 5) Manual overrides / product integration
**Responsibilities**
- Allow explicit overrides (`layout`, `buttons`, visibility).
- Inject context state (`game_over`, `menu`).

**Why here**
- Product decisions and UX constraints are not reliably inferred.
- Overrides keep behavior deterministic under known conditions.

## Concrete Examples (Best Layer Placement)

### Control-space decoupling (rate vs magnitude)
- **LLM**: label `control_space`.
- **Update script**: validate enum (no inference beyond schema).
- **Library**: decouple axes into separate controls.
**Why**: semantics belong in LLM; layout belongs in library.

### Discrete vs continuous movement
- **LLM**: preferred source of truth (movement semantics).
- **Update script**: conservative fallback (`detect_discrete_move`).
- **Library**: render digital D-pad when discrete.
**Why**: LLM may miss; fallback is deterministic and safe.

### Contextual/utility actions (restart, pause)
- **LLM**: label `importance` + `context`.
- **Update script**: validate enums.
- **Library**: move utility actions to non-primary space; hide if context-specific.
**Why**: semantics are inferred, layout is deterministic.

### Existing touch UI detection
- **Update script**: optional static hint flag only.
- **Library runtime**: actual detection and suppression.
**Why**: requires DOM and viewport awareness.

## How This Stays Generalizable
Every rule is based on:
- input topology,
- control semantics,
- and ergonomics,
not genre names. That ensures layouts generalize across games while remaining deterministic.
