#!/usr/bin/env python3
"""
Run a one-shot single-file game audit using OpenRouter directly.

Reads HTML source, sends it to OpenRouter with audit instructions, and writes:
1) Parsed JSON audit output (--out-file)
2) Full raw OpenRouter response (--raw-file, optional)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_SORT = "price"
DEFAULT_MAX_TOKENS = 6000


SYSTEM_PROMPT = (
    "You are a senior game-quality auditor. "
    "Return valid JSON only and no markdown."
)


def load_env_value(env_path: Path, key: str) -> Optional[str]:
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() != key:
            continue
        value = v.strip()
        if len(value) >= 2 and (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ):
            value = value[1:-1]
        return value.strip()
    return None


def build_user_prompt(html_source: str) -> str:
    return f"""# Task: Audit a single-file web game for gameplay quality, cross-device playability, lifecycle safety, and performance

You are auditing one complete game file. Read the entire code and produce a structured audit.

## Full source code
```html
{html_source}
```

## Primary objective
Find real, user-impacting issues. Be strict about correctness and practical gameplay behavior.

## Required audit checks (check all 10)
1. `dt_required_for_raf`
- Detect frame-rate-dependent logic in `requestAnimationFrame` loops.
- Red flags: `% 60` assumptions, `counter++` timers, fixed per-frame movement/decay not multiplied by elapsed time.

2. `listener_registration_safety`
- Detect event listener stacking or duplicate registration risk in start/restart/init flows.

3. `timer_timeout_cleanup`
- Detect intervals/timeouts that can survive game-over/restart/navigation and trigger stale behavior.

4. `touch_playability_minimum`
- Detect keyboard-only or desktop-only controls (e.g., right-click-only mechanics) without touch fallback.

5. `responsive_basics`
- Detect fixed dimensions and layout clipping risks on smaller screens.
- Check viewport meta, overflow clipping, fixed grid/canvas sizing.

6. `unbounded_collection_growth`
- Detect arrays/objects that grow over time without cap/TTL/cleanup (entities, effects, collectibles, etc).

7. `mutation_during_iteration`
- Detect unsafe mutation while iterating (splice/filter during loops that can skip elements or cause logic bugs).

8. `audio_hotpath_allocations`
- Detect `new Audio(...)` or expensive media allocation in hot paths (loop/rapid handlers) that can stutter.

9. `restart_state_reset_completeness`
- Detect run-scoped state that is initialized once but not reset on restart/new run.

10. `collision_formula_sanity`
- Detect suspicious collision checks (too strict/too loose, single-size check where two-body overlap is expected).

## Severity rubric
- `high`: breaks gameplay fairness, major cross-device failure, serious lifecycle/perf issue likely visible to users.
- `medium`: clear gameplay/UX/perf risk but not always catastrophic.
- `low`: polish issue or edge case with limited impact.

## Output requirements
1. Output valid JSON only (no markdown outside JSON).
2. Include only issues with concrete evidence from code.
3. Every finding must include:
- `check_id` (one of the 10 check IDs above)
- `severity` (`high|medium|low`)
- `title`
- `evidence` (exact code snippets or precise references)
- `impact` (user-visible consequence)
- `fix_plan` (specific technical change, not generic advice)
- `autofix_candidate` (`true|false`)
4. If a check has no finding, list it under `checks_passed`.

## JSON schema
{{
  "risk_score": 0,
  "summary": {{
    "critical_findings": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  }},
  "playability": {{
    "desktop": "good|mixed|poor",
    "touch": "good|mixed|poor",
    "responsiveness": "good|mixed|poor",
    "performance_long_run": "good|mixed|poor"
  }},
  "findings": [
    {{
      "check_id": "dt_required_for_raf",
      "severity": "high",
      "title": "Frame-rate-dependent hunger drain",
      "evidence": [
        "if (survivalTimer % 60 === 0) {{ ... }}",
        "hunger = Math.max(0, hunger - hungerDecreaseRate);"
      ],
      "impact": "Gameplay speed varies by refresh rate and CPU load.",
      "fix_plan": "Introduce delta-time and scale hunger/score updates by elapsed seconds.",
      "autofix_candidate": true
    }}
  ],
  "checks_passed": [
    "mutation_during_iteration"
  ],
  "top_3_priority_fixes": [
    "..."
  ]
}}

## Important constraints
- Do not invent missing code.
- Do not assume runtime behavior that is unsupported by evidence.
- Prefer fewer, high-confidence findings over many weak findings.
- Be explicit when behavior depends on frame rate, screen size, or input modality.
"""


def extract_message_content(openrouter_response: dict[str, Any]) -> str:
    choices = openrouter_response.get("choices") or []
    if not choices:
        return ""
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
            elif isinstance(part, str):
                chunks.append(part)
        return "\n".join(chunks)
    return ""


def strip_code_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return s


def find_first_json_object(text: str) -> Optional[dict[str, Any]]:
    s = strip_code_fence(text)
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    n = len(s)
    for start in range(n):
        if s[start] != "{":
            continue
        depth = 0
        in_str = False
        escape = False
        for i in range(start, n):
            ch = s[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = s[start : i + 1]
                    try:
                        obj = json.loads(candidate)
                        if isinstance(obj, dict):
                            return obj
                    except Exception:
                        break
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run OpenRouter game audit on a full HTML file."
    )
    parser.add_argument("--html-file", required=True, help="Path to source HTML file")
    parser.add_argument("--out-file", required=True, help="Path to write parsed audit JSON")
    parser.add_argument(
        "--raw-file",
        default="",
        help="Optional path to write full raw OpenRouter response JSON",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id")
    parser.add_argument(
        "--provider-sort",
        default=DEFAULT_SORT,
        choices=["price", "throughput", "latency"],
        help="OpenRouter provider sort mode",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Max completion tokens"
    )
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    parser.add_argument(
        "--timeout-seconds", type=int, default=300, help="HTTP timeout in seconds"
    )
    parser.add_argument(
        "--disable-reasoning",
        action="store_true",
        help="Disable reasoning parameter",
    )
    args = parser.parse_args()

    root_env = Path(".env")
    key = os.environ.get("OPENROUTER_API_KEY") or load_env_value(root_env, "OPENROUTER_API_KEY")
    if not key:
        print("ERROR: OPENROUTER_API_KEY not found in environment or .env", file=sys.stderr)
        return 2

    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"ERROR: html file not found: {html_path}", file=sys.stderr)
        return 2

    out_path = Path(args.out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html_source = html_path.read_text(encoding="utf-8", errors="replace")
    user_prompt = build_user_prompt(html_source)

    payload: dict[str, Any] = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "provider": {
            "sort": args.provider_sort,
            "allow_fallbacks": True,
            "data_collection": "deny",
        },
    }
    if not args.disable_reasoning:
        payload["reasoning"] = {"enabled": True, "effort": "high"}

    req = Request(
        OPENROUTER_URL,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://fuzzycode.dev",
            "X-Title": "Fuzzycode Page Audits",
        },
    )

    try:
        with urlopen(req, timeout=args.timeout_seconds) as response:
            raw_text = response.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP ERROR {e.code}", file=sys.stderr)
        print(err_body, file=sys.stderr)
        return 1
    except URLError as e:
        print(f"NETWORK ERROR: {e}", file=sys.stderr)
        return 1

    try:
        raw_response_json = json.loads(raw_text)
    except json.JSONDecodeError:
        print("ERROR: OpenRouter returned non-JSON response", file=sys.stderr)
        print(raw_text[:1000], file=sys.stderr)
        return 1

    if args.raw_file:
        raw_path = Path(args.raw_file)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(
            json.dumps(raw_response_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    usage = raw_response_json.get("usage", {})
    total_cost = usage.get("total_cost")
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    provider_used = raw_response_json.get("model")

    content = extract_message_content(raw_response_json)
    parsed = find_first_json_object(content)
    if parsed is None:
        print("ERROR: Could not parse model output as JSON object", file=sys.stderr)
        print("MODEL_OUTPUT_PREVIEW:", file=sys.stderr)
        print(content[:2000], file=sys.stderr)
        return 1

    out_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote audit JSON: {out_path}")
    if args.raw_file:
        print(f"Wrote raw response: {args.raw_file}")
    print(
        "OpenRouter usage:",
        json.dumps(
            {
                "provider_model": provider_used,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost_usd": total_cost,
            }
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

