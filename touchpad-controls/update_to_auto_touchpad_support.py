#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Optional, Tuple
from pathlib import Path

DEFAULT_CODEX_MODEL = "gpt-5.1-codex-mini"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_CODEX_REASONING = "high"
DEFAULT_GROQ_REASONING = "medium"
DEFAULT_GROQ_MAX_TOKENS = 32768
DEFAULT_GROQ_ENDPOINT = "auto"
DEFAULT_GROQ_USER_AGENT = "Mozilla/5.0 (compatible; FuzzycodeTouchpad/1.0)"
PROMPT_TEMPLATE_PATH = Path("prompts/pipeline_prompt_template.md")
NIPPLEJS_CDN = "https://cdn.jsdelivr.net/npm/nipplejs@0.10.2/dist/nipplejs.js"
GROQ_CHAT_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_RESPONSES_API_URL = "https://api.groq.com/openai/v1/responses"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a game HTML file with Codex and inject touchpad controls."
    )
    parser.add_argument("--game", required=True, help="Path to the game HTML file.")
    parser.add_argument(
        "--output",
        help="Output HTML path. Defaults to <game>_touch.html or _touch_embedded.html if --embed-lib is set."
    )
    parser.add_argument(
        "--embed-lib",
        action="store_true",
        help="Inline touchpad-controls.js into the output HTML (single-output mode)."
    )
    parser.add_argument(
        "--embed-json",
        action="store_true",
        help="Embed the raw JSON output as a script tag for traceability."
    )
    parser.add_argument(
        "--debug-layout",
        action="store_true",
        help="Log the computed layout summary in the browser console."
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow empty bindings without failing (useful for mouse-only games)."
    )
    parser.add_argument(
        "--prompt-template",
        default=str(PROMPT_TEMPLATE_PATH),
        help="Path to the prompt template markdown file."
    )
    parser.add_argument(
        "--provider",
        choices=["groq", "codex"],
        default="groq",
        help="LLM provider to use (default: groq)."
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to use for the selected provider."
    )
    parser.add_argument(
        "--reasoning-effort",
        default=None,
        help="Reasoning effort for the selected provider."
    )
    parser.add_argument(
        "--groq-endpoint",
        choices=["auto", "chat", "responses"],
        default=DEFAULT_GROQ_ENDPOINT,
        help="Groq API endpoint to use (auto chooses responses for openai/gpt-oss models)."
    )
    parser.add_argument(
        "--groq-max-completion-tokens",
        type=int,
        default=DEFAULT_GROQ_MAX_TOKENS,
        help=(
            "Max completion tokens for Groq "
            f"(chat: max_completion_tokens, responses: max_output_tokens; default: {DEFAULT_GROQ_MAX_TOKENS})."
        )
    )
    parser.add_argument(
        "--groq-user-agent",
        default=DEFAULT_GROQ_USER_AGENT,
        help="User-Agent header to send to Groq (may avoid Cloudflare 1010 blocks)."
    )
    return parser.parse_args()


def next_run_id(llm_dir: Path) -> int:
    pattern = re.compile(r"run_(\d+)_prompt\.md")
    max_id = 0
    for path in llm_dir.glob("run_*_prompt.md"):
        match = pattern.match(path.name)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return max_id + 1


def render_prompt(template_path: Path, game_path: Path) -> str:
    template = template_path.read_text()
    html_content = game_path.read_text()
    prompt = template.replace("{{GAME_FILE}}", game_path.name)
    return prompt.replace("{{GAME_HTML}}", html_content)


def run_codex(prompt_text: str, output_path: Path, model: str, effort: str) -> None:
    command = [
        "codex",
        "exec",
        "-m",
        model,
        "-c",
        f"model_reasoning_effort=\"{effort}\"",
        "--skip-git-repo-check",
        "--output-last-message",
        str(output_path),
        "-"
    ]

    result = subprocess.run(
        command,
        input=prompt_text,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError("codex exec failed; see output above.")


def load_env_file(path: Path) -> dict:
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith("\"") and value.endswith("\"")) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        else:
            if "#" in value:
                value = value.split("#", 1)[0].strip()
        values[key] = value
    return values


def load_env_chain() -> dict:
    search_paths = []
    script_dir = Path(__file__).resolve().parent
    search_paths.append(script_dir / ".env")
    search_paths.append(script_dir.parent / ".env")

    cwd = Path.cwd()
    if cwd != script_dir:
        search_paths.append(cwd / ".env")
    if cwd.parent != script_dir.parent:
        search_paths.append(cwd.parent / ".env")

    for path in search_paths:
        if path.exists():
            return load_env_file(path)
    return {}


def get_groq_api_key() -> str:
    if os.getenv("GROQ_API_KEY"):
        return os.environ["GROQ_API_KEY"]
    env_values = load_env_chain()
    api_key = env_values.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not found in environment or .env file.")
    return api_key


class GroqAPIError(RuntimeError):
    def __init__(self, endpoint: str, code: int, body: str) -> None:
        super().__init__(f"{endpoint} {code} {body}")
        self.endpoint = endpoint
        self.code = code
        self.body = body


def pick_groq_endpoint(model: str, endpoint_choice: str) -> str:
    if endpoint_choice != "auto":
        return endpoint_choice
    if model.startswith("openai/gpt-oss"):
        return "responses"
    return "chat"


def build_groq_payload(
    prompt_text: str,
    model: str,
    effort: str,
    max_tokens: int,
    endpoint: str
) -> dict:
    payload = {
        "model": model,
        "temperature": 0
    }
    if endpoint == "responses":
        payload["input"] = prompt_text
        payload["max_output_tokens"] = max_tokens
    else:
        payload["messages"] = [{"role": "user", "content": prompt_text}]
        payload["max_completion_tokens"] = max_tokens
    if effort and endpoint == "chat":
        payload["reasoning_effort"] = effort
    return payload


def request_groq(api_url: str, payload: dict, endpoint: str, api_key: str, user_agent: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8") if exc.fp else ""
        raise GroqAPIError(endpoint, exc.code, error_body) from exc


def request_groq_with_retry(
    api_url: str,
    payload: dict,
    endpoint: str,
    api_key: str,
    user_agent: str
) -> dict:
    try:
        return request_groq(api_url, payload, endpoint, api_key, user_agent)
    except GroqAPIError as exc:
        if "reasoning_effort" not in payload:
            raise
        retry_payload = dict(payload)
        retry_payload.pop("reasoning_effort", None)
        try:
            response_json = request_groq(api_url, retry_payload, endpoint, api_key, user_agent)
            print(
                "Warning: Groq API rejected reasoning_effort; retried without it.",
                file=sys.stderr
            )
            return response_json
        except GroqAPIError as retry_exc:
            raise retry_exc from exc


def extract_groq_content(response_json: dict) -> str:
    choices = response_json.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    item_type = item.get("type")
                    if item_type and item_type not in ("output_text", "text"):
                        continue
                    text = item.get("text") or item.get("content")
                    if text:
                        parts.append(text)
            if parts:
                return "".join(parts).strip()

    output_text = response_json.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = response_json.get("output")
    if isinstance(output, list):
        message_items = [item for item in output if isinstance(item, dict) and item.get("type") == "message"]
        if message_items:
            output = message_items
        parts = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content_list = item.get("content")
            if not isinstance(content_list, list):
                continue
            for chunk in content_list:
                if not isinstance(chunk, dict):
                    continue
                chunk_type = chunk.get("type")
                if chunk_type and chunk_type not in ("output_text", "text"):
                    continue
                text = chunk.get("text")
                if text:
                    parts.append(text)
        if parts:
            return "\n".join(parts).strip()
    return ""


def run_groq(
    prompt_text: str,
    output_path: Path,
    model: str,
    effort: str,
    max_tokens: int,
    endpoint_choice: str,
    user_agent: str,
    response_path: Optional[Path] = None
) -> None:
    api_key = get_groq_api_key()
    primary_endpoint = pick_groq_endpoint(model, endpoint_choice)
    endpoints = [primary_endpoint]
    if endpoint_choice == "auto":
        endpoints.append("chat" if primary_endpoint == "responses" else "responses")

    errors = []
    for endpoint in endpoints:
        api_url = GROQ_RESPONSES_API_URL if endpoint == "responses" else GROQ_CHAT_API_URL
        payload = build_groq_payload(prompt_text, model, effort, max_tokens, endpoint)
        try:
            response_json = request_groq_with_retry(
                api_url,
                payload,
                endpoint,
                api_key,
                user_agent
            )
        except GroqAPIError as exc:
            errors.append(f"{exc.endpoint} {exc.code} {exc.body}")
            continue

        if response_path is not None:
            response_blob = {
                "endpoint": endpoint,
                "response": response_json
            }
            response_path.write_text(json.dumps(response_blob, indent=2))

        content = extract_groq_content(response_json)
        if content:
            output_path.write_text(content)
            if endpoint_choice == "auto" and endpoint != primary_endpoint:
                print(f"Warning: Groq API succeeded via {endpoint} after fallback.", file=sys.stderr)
            return
        errors.append(f"{endpoint} response missing content")

    raise RuntimeError("Groq API error: " + " | ".join(errors))


def escape_script(content: str) -> str:
    return content.replace("</script", "<\\/script")


def build_injection(
    bindings: dict,
    layout: str,
    action_meta: dict,
    embed_lib: bool,
    embed_json: bool,
    debug_layout: bool
) -> str:
    script_blocks = []
    script_blocks.append(
        f'<script src="{NIPPLEJS_CDN}" crossorigin="anonymous"></script>'
    )

    if embed_lib:
        lib_path = Path("touchpad-controls.js")
        if not lib_path.exists():
            raise FileNotFoundError("touchpad-controls.js not found in the current directory.")
        lib_content = escape_script(lib_path.read_text())
        script_blocks.append("<script>\n" + lib_content + "\n</script>")
    else:
        script_blocks.append('<script src="./touchpad-controls.js"></script>')

    if embed_json:
        json_payload = {"layout": layout, "bindings": bindings}
        if action_meta:
            json_payload["action_meta"] = action_meta
        json_blob = json.dumps(json_payload, indent=2)
        script_blocks.append(
            '<script type="application/json" id="touchpad-bindings-json">\n'
            + json_blob
            + "\n</script>"
        )

    bindings_json = json.dumps(bindings, indent=4)
    action_meta_json = json.dumps(action_meta or {}, indent=4)
    debug_line = "        debug: true,\n" if debug_layout else ""
    script_blocks.append(
        "<script>\n"
        "    const touchBindings = " + bindings_json.replace("\n", "\n    ") + ";\n"
        "    const touchActionMeta = " + action_meta_json.replace("\n", "\n    ") + ";\n\n"
        "    TouchpadControls.create({\n"
        f"        layout: {json.dumps(layout)},\n"
        "        bindings: touchBindings,\n"
        "        actionMeta: touchActionMeta"
        + (",\n" + debug_line if debug_layout else "\n")
        + "    });\n"
        "</script>"
    )

    return "\n    ".join(script_blocks)


def inject_controls(source_html: str, injection: str) -> str:
    if "TouchpadControls.create" in source_html:
        raise ValueError("TouchpadControls.create already present; refusing to double-inject.")

    if "</body>" not in source_html:
        raise ValueError("Missing </body> tag; cannot inject safely.")

    return source_html.replace("</body>", "\n    " + injection + "\n</body>")


def detect_discrete_move(source_html: str, bindings: dict, action_meta: dict) -> bool:
    move = bindings.get("move") if isinstance(bindings, dict) else None
    if not isinstance(move, dict):
        return False
    move_meta = action_meta.get("move") if isinstance(action_meta, dict) else None
    # Only infer when LLM did not provide a behavior label.
    if isinstance(move_meta, dict) and move_meta.get("behavior"):
        return False

    html_lower = source_html.lower()
    if "keydown" not in html_lower:
        return False

    lines = source_html.splitlines()
    keyup_indices = [i for i, line in enumerate(lines) if "keyup" in line.lower()]
    if not keyup_indices:
        return True

    arrow_tokens = {"arrowleft", "arrowright", "arrowup", "arrowdown"}
    wasd_tokens = {"keya", "keyd", "keyw", "keys"}
    keycode_tokens = {"37", "38", "39", "40", "65", "68", "87", "83"}
    key_state_patterns = ("keys[", "keystate", "pressedkeys", "pressed_keys", "keypressed", "keyspressed")

    for idx in keyup_indices:
        window = "\n".join(lines[idx:idx + 6]).lower()
        if any(token in window for token in key_state_patterns):
            return False
        if any(token in window for token in arrow_tokens | wasd_tokens):
            return False
        if "keycode" in window or "which" in window:
            if any(code in window for code in keycode_tokens):
                return False

    return True


def sanitize_action_meta(action_meta: dict) -> dict:
    if not isinstance(action_meta, dict):
        return {}

    allowed_kind = {"axis", "button"}
    allowed_behavior = {"continuous", "discrete"}
    allowed_interaction = {"tap", "hold", "repeat"}
    allowed_control_space = {"vector", "rate", "magnitude"}
    allowed_activation = {"hold", "latch"}
    allowed_direction_mode = {"vector", "cardinal"}
    allowed_granularity = {"fine", "coarse"}
    allowed_pair_position = {"left", "right"}

    sanitized = {}
    for action, meta in action_meta.items():
        if not isinstance(meta, dict):
            continue
        cleaned = {}
        for key, value in meta.items():
            if key == "kind" and value in allowed_kind:
                cleaned[key] = value
            elif key == "behavior" and value in allowed_behavior:
                cleaned[key] = value
            elif key == "interaction" and value in allowed_interaction:
                cleaned[key] = value
            elif key == "activation" and value in allowed_activation:
                cleaned[key] = value
            elif key == "direction_mode" and value in allowed_direction_mode:
                cleaned[key] = value
            elif key == "granularity" and value in allowed_granularity:
                cleaned[key] = value
            elif key == "simultaneous" and isinstance(value, bool):
                cleaned[key] = value
            elif key == "control_space" and value in allowed_control_space:
                cleaned[key] = value
            elif key == "pair_id" and isinstance(value, str):
                cleaned[key] = value
            elif key == "pair_position" and value in allowed_pair_position:
                cleaned[key] = value
        if cleaned:
            sanitized[action] = cleaned
    return sanitized


def extract_meta(spec: dict, kind: str) -> dict:
    meta = {}
    if isinstance(spec, dict):
        for field in (
            "behavior",
            "interaction",
            "simultaneous",
            "control_space",
            "activation",
            "direction_mode",
            "granularity",
            "pair_id",
            "pair_position"
        ):
            if field in spec:
                meta[field] = spec[field]
    if kind:
        meta["kind"] = kind
    return meta


def extract_action_keys(spec):
    if isinstance(spec, dict):
        if "keys" in spec:
            return spec["keys"]
        if "key" in spec:
            return spec["key"]
    return spec


def select_single_key(keys: dict) -> Optional[str]:
    if not isinstance(keys, dict):
        return None
    for name in ("up", "right", "down", "left"):
        key = keys.get(name)
        if key:
            return key
    return None


def axis_priority(axis: dict) -> Tuple[int, int]:
    priority = axis.get("priority")
    if priority == "primary":
        priority_score = 2
    elif priority == "secondary":
        priority_score = 1
    else:
        priority_score = 0

    control_space = axis.get("control_space")
    if control_space == "vector":
        control_score = 2
    elif control_space == "rate":
        control_score = 1
    else:
        control_score = 0

    return (priority_score, control_score)


def extract_bindings_from_axes_actions(data: dict) -> Tuple[Optional[dict], Optional[dict]]:
    axes = data.get("axes")
    actions = data.get("actions")
    if not isinstance(axes, list) and not isinstance(actions, dict):
        return None, None

    bindings = {}
    action_meta = {}

    if isinstance(actions, dict):
        for role, spec in actions.items():
            keys = extract_action_keys(spec)
            if keys is None:
                continue
            bindings[role] = keys
            meta = extract_meta(spec, "button")
            if meta:
                action_meta[role] = meta

    movement_axes = []
    aim_axes = []

    if isinstance(axes, list):
        for axis in axes:
            if not isinstance(axis, dict):
                continue
            keys = axis.get("keys")
            if not isinstance(keys, dict):
                continue
            usage = axis.get("usage")
            control_space = axis.get("control_space")

            if usage not in ("movement", "aim"):
                continue

            if control_space == "magnitude":
                if "magnitude" in bindings:
                    continue
                mag_key = select_single_key(keys)
                if not mag_key:
                    continue
                bindings["magnitude"] = mag_key
                mag_meta = extract_meta(axis, "button")
                mag_meta["control_space"] = "magnitude"
                action_meta["magnitude"] = mag_meta
                continue

            if usage == "movement":
                movement_axes.append(axis)
            elif usage == "aim":
                aim_axes.append(axis)

    def build_axis_mapping(axis: dict) -> tuple[dict, dict]:
        keys = axis.get("keys")
        meta = extract_meta(axis, "axis")
        control_space = axis.get("control_space")
        if control_space:
            meta["control_space"] = control_space
        return keys, meta

    if movement_axes:
        movement_axes.sort(key=axis_priority, reverse=True)
        move_keys, move_meta = build_axis_mapping(movement_axes[0])
        bindings["move"] = move_keys
        if move_meta:
            action_meta["move"] = move_meta

        if aim_axes:
            aim_axes.sort(key=axis_priority, reverse=True)
            aim_keys, aim_meta = build_axis_mapping(aim_axes[0])
            bindings["aim"] = aim_keys
            if aim_meta:
                action_meta["aim"] = aim_meta
    elif aim_axes:
        aim_axes.sort(key=axis_priority, reverse=True)
        move_keys, move_meta = build_axis_mapping(aim_axes[0])
        bindings["move"] = move_keys
        if move_meta:
            action_meta["move"] = move_meta

        if len(aim_axes) > 1:
            aim_keys, aim_meta = build_axis_mapping(aim_axes[1])
            bindings["aim"] = aim_keys
            if aim_meta:
                action_meta["aim"] = aim_meta

    return bindings, action_meta


def main() -> None:
    args = parse_args()

    game_path = Path(args.game)
    if not game_path.exists():
        raise FileNotFoundError(f"Game file not found: {game_path}")

    llm_dir = Path("llm_runs")
    llm_dir.mkdir(parents=True, exist_ok=True)

    template_path = Path(args.prompt_template)
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    provider = args.provider
    model = args.model
    reasoning_effort = args.reasoning_effort

    if provider == "groq":
        if model is None:
            model = DEFAULT_GROQ_MODEL
        if reasoning_effort is None:
            reasoning_effort = DEFAULT_GROQ_REASONING
    else:
        if model is None:
            model = DEFAULT_CODEX_MODEL
        if reasoning_effort is None:
            reasoning_effort = DEFAULT_CODEX_REASONING

    run_id = next_run_id(llm_dir)
    run_prefix = f"run_{run_id:03d}"
    prompt_path = llm_dir / f"{run_prefix}_prompt.md"
    output_path = llm_dir / f"{run_prefix}_output.json"
    response_path = llm_dir / f"{run_prefix}_response.json"

    prompt_text = render_prompt(template_path, game_path)
    prompt_path.write_text(prompt_text)

    if provider == "groq":
        run_groq(
            prompt_text,
            output_path,
            model,
            reasoning_effort,
            args.groq_max_completion_tokens,
            args.groq_endpoint,
            args.groq_user_agent,
            response_path
        )
    else:
        run_codex(prompt_text, output_path, model, reasoning_effort)

    raw_output = output_path.read_text().strip()
    if not raw_output:
        raise RuntimeError("Codex output was empty.")

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Codex output is not valid JSON: {exc}") from exc

    layout = data.get("layout") or "auto"

    bindings, action_meta = extract_bindings_from_axes_actions(data)
    if bindings is None:
        bindings = data.get("bindings")
        action_meta = data.get("action_meta") or data.get("actionMeta") or {}

    if not isinstance(bindings, dict):
        if args.allow_empty:
            print(
                "Warning: LLM output missing bindings; proceeding with empty bindings.",
                file=sys.stderr
            )
            bindings = {}
        else:
            raise RuntimeError("No bindings found in Codex output.")
    elif not bindings:
        if args.allow_empty:
            bindings = {}
        else:
            raise RuntimeError("No bindings found in Codex output.")

    action_meta = sanitize_action_meta(action_meta or {})

    source_html = game_path.read_text()
    if detect_discrete_move(source_html, bindings, action_meta):
        print(
            "Warning: move.behavior missing; inferred discrete movement from HTML heuristics.",
            file=sys.stderr
        )
        action_meta = dict(action_meta)
        move_meta = dict(action_meta.get("move") or {})
        move_meta.setdefault("kind", "axis")
        move_meta["behavior"] = "discrete"
        move_meta.setdefault("interaction", "tap")
        action_meta["move"] = move_meta
        if layout == "auto" and not bindings.get("aim"):
            layout = "digital-dpad"
    output_paths = []
    embed_flags = []

    if args.output:
        output_paths.append(Path(args.output))
        embed_flags.append(args.embed_lib)
    elif args.embed_lib:
        output_paths.append(game_path.with_name(game_path.stem + "_touch_embedded.html"))
        embed_flags.append(True)
    else:
        output_paths.append(game_path.with_name(game_path.stem + "_touch.html"))
        embed_flags.append(False)
        output_paths.append(game_path.with_name(game_path.stem + "_touch_embedded.html"))
        embed_flags.append(True)

    for output_path_html, embed_lib in zip(output_paths, embed_flags):
        injection = build_injection(
            bindings,
            layout,
            action_meta,
            embed_lib,
            args.embed_json,
            args.debug_layout
        )
        output_html = inject_controls(source_html, injection)
        output_path_html.write_text(output_html)
        print(f"Wrote: {output_path_html}")
    print(f"Prompt: {prompt_path}")
    print(f"Output JSON: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
