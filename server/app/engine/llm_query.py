"""AI Smart Mode query generation via OpenRouter."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import httpx

from .schema_context import AI_SYSTEM_PROMPT, AI_USER_PROMPT_TEMPLATE

OPENROUTER_API_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
PRIMARY_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "openai/gpt-4o-mini")
REQUEST_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT", "12"))
RESPONSE_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "800"))


class LLMQueryError(RuntimeError):
    """Raised when the LLM cannot satisfy the request."""


@dataclass
class LLMQueryResult:
    sql: str
    summary: str
    follow_ups: List[str]
    raw: Dict[str, Any]
    model: str


_DOTENV_LOADED = False


def _load_dotenv() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    dotenv_path = os.getenv("OPENROUTER_DOTENV")
    if not dotenv_path:
        from pathlib import Path

        # Default to server/.env relative to this file
        dotenv_path = str(Path(__file__).resolve().parents[2] / ".env")

    try:
        with open(dotenv_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
    except FileNotFoundError:
        pass
    finally:
        _DOTENV_LOADED = True


def _build_headers() -> Dict[str, str]:
    _load_dotenv()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise LLMQueryError("OPENROUTER_API_KEY is not configured")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    referer = os.getenv("OPENROUTER_SITE_URL")
    if referer:
        headers["HTTP-Referer"] = referer
    app_name = os.getenv("OPENROUTER_APP_NAME")
    if app_name:
        headers["X-Title"] = app_name
    return headers


def _format_filters(filters: Optional[Dict[str, Any]]) -> str:
    if not filters:
        return "none"
    try:
        return json.dumps(filters, ensure_ascii=False)
    except Exception:
        return str(filters)


def _build_messages(question: str, filters: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    user_prompt = AI_USER_PROMPT_TEMPLATE.format(question=question, filters=_format_filters(filters))
    return [
        {"role": "system", "content": AI_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _request_payload(model: str, messages: Sequence[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "model": model,
        "messages": list(messages),
        "temperature": 0,
        "max_tokens": RESPONSE_MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }


def _call_openrouter(model: str, messages: Sequence[Dict[str, str]]) -> Dict[str, Any]:
    url = f"{OPENROUTER_API_URL.rstrip('/')}/chat/completions"
    payload = _request_payload(model, messages)
    headers = _build_headers()

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.post(url, headers=headers, json=payload)
    if response.status_code >= 400:
        raise LLMQueryError(f"OpenRouter returned {response.status_code}: {response.text[:200]}")
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMQueryError(f"Malformed OpenRouter response: {data}") from exc
    return {
        "model": data.get("model", model),
        "content": content,
        "raw": data,
    }


def _parse_content(content: Any) -> Dict[str, Any]:
    if isinstance(content, list):
        # Some providers return list of content parts, join them
        text = "".join(part if isinstance(part, str) else part.get("text", "") for part in content)
    else:
        text = str(content)
    text = text.strip()
    if not text:
        raise LLMQueryError("LLM returned empty content")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMQueryError(f"LLM response was not valid JSON: {text[:200]}") from exc


def run(message: str, filters: Optional[Dict[str, Any]] = None) -> LLMQueryResult:
    """Generate SQL for the given message using the configured LLM."""
    question = message.strip()
    if not question:
        raise LLMQueryError("Prompt is empty")

    messages = _build_messages(question, filters)
    attempts: List[str] = [PRIMARY_MODEL]
    if FALLBACK_MODEL and FALLBACK_MODEL != PRIMARY_MODEL:
        attempts.append(FALLBACK_MODEL)

    last_error: Optional[Exception] = None
    for model in attempts:
        try:
            response = _call_openrouter(model, messages)
            parsed = _parse_content(response["content"])
            sql = str(parsed.get("sql", "")).strip()
            summary = str(parsed.get("summary", "")).strip()
            follow_ups_raw = parsed.get("follow_ups") or []
            if isinstance(follow_ups_raw, str):
                follow_ups = [follow_ups_raw.strip()] if follow_ups_raw.strip() else []
            else:
                follow_ups = [str(item).strip() for item in follow_ups_raw if str(item).strip()]
            return LLMQueryResult(
                sql=sql,
                summary=summary,
                follow_ups=follow_ups,
                raw={
                    "model": response.get("model", model),
                    "messages": messages,
                    "response": parsed,
                },
                model=response.get("model", model),
            )
        except Exception as exc:  # pylint: disable=broad-except
            last_error = exc
            continue

    raise LLMQueryError(str(last_error) if last_error else "LLM generation failed")
