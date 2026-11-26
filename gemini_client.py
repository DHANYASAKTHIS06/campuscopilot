"""
AcadFlow — Centralized Google Gemini Configuration & Client
Uses the official `google-genai` SDK as the sole LLM provider.
"""
import os
import time
from dotenv import load_dotenv

load_dotenv()

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
REQUEST_TIMEOUT_MS = 60_000  # 60 seconds
MAX_RETRIES = 2

_client = None
_client_key_hash = None


def _read_config(name: str, default: str = "") -> str:
    val = os.getenv(name)
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(name)
        except Exception:
            val = None
    cleaned = (val or default).strip().strip('"').strip("'")
    return cleaned


def get_api_key() -> str:
    key = _read_config("GEMINI_API_KEY")
    if not key or key.startswith("YOUR_") or key.startswith("your-"):
        return ""
    return key


def get_model() -> str:
    return _read_config("GEMINI_MODEL", DEFAULT_GEMINI_MODEL) or DEFAULT_GEMINI_MODEL


def has_api_key() -> bool:
    return bool(get_api_key())


def get_status() -> dict:
    """Return non-sensitive AI configuration status for Admin monitoring."""
    key = get_api_key()
    return {
        "provider": "Google Gemini (google-genai)",
        "configured": bool(key),
        "model": get_model(),
    }


def _get_client():
    global _client, _client_key_hash
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your environment."
        )
    key_hash = hash(key)
    if _client is None or _client_key_hash != key_hash:
        from google import genai
        from google.genai import types
        _client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )
        _client_key_hash = key_hash
    return _client


def _classify_error(exc: Exception) -> tuple[str, bool]:
    """
    Map Gemini SDK/HTTP exceptions to safe user-facing messages (never exposing API keys).
    Returns (user_message, is_retryable).
    """
    raw = str(exc)
    low = raw.lower()

    if any(tok in low for tok in ("api_key_invalid", "invalid api key", "api key not valid", "401", "403", "permission_denied", "unauthenticated")):
        return (
            "Gemini API authentication failed. Please verify that GEMINI_API_KEY is valid and active.",
            False,
        )
    if any(tok in low for tok in ("429", "resource_exhausted", "quota", "rate limit", "too many requests")):
        return (
            "Gemini API rate limit or quota exceeded. Please wait a moment and retry.",
            True,
        )
    if any(tok in low for tok in ("404", "not_found", "model not found", "is not supported", "unsupported")):
        return (
            f"The configured Gemini model ('{get_model()}') is unsupported or unavailable. "
            "Check GEMINI_MODEL in your environment settings.",
            False,
        )
    if any(tok in low for tok in ("timeout", "timed out", "deadline_exceeded", "500", "502", "503", "504", "unavailable", "connection")):
        return (
            "Temporary connection issue while reaching Google Gemini. Please retry in a moment.",
            True,
        )
    return ("Unable to complete AI request right now. Please try again.", False)


def generate_chat(system: str, messages: list[dict], max_tokens: int = 1500) -> str:
    """
    Call Google Gemini with system instruction and multi-turn messages:
      messages = [{"role": "user"|"assistant", "content": "..."}]
    Retries transient failures with exponential backoff.
    """
    try:
        from google.genai import types
        client = _get_client()
        model = get_model()
    except Exception as e:
        msg, _ = _classify_error(e)
        return f"[AI Error: {str(e) if 'not configured' in str(e) else msg}]"

    contents = []
    for m in messages:
        role = "model" if m.get("role") in ("assistant", "model", "ai") else "user"
        text = (m.get("content") or "").strip()
        if not text:
            continue
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
        )

    if not contents:
        return "[AI Error: Empty prompt.]"

    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens,
        temperature=0.2,
    )

    last_msg = "Unable to reach Google Gemini."
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            text = (getattr(resp, "text", None) or "").strip()
            if text:
                return text
            # Fallback if parts exist
            if getattr(resp, "candidates", None):
                parts = []
                for cand in resp.candidates:
                    if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                        for p in cand.content.parts:
                            if getattr(p, "text", None):
                                parts.append(p.text)
                if parts:
                    return "".join(parts).strip()
            return "[AI Error: Gemini returned an empty response. Please try rephrasing.]"
        except Exception as e:
            msg, retryable = _classify_error(e)
            last_msg = msg
            if retryable and attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue
            return f"[AI Error: {msg}]"

    return f"[AI Error: {last_msg}]"


def generate_text(system: str, user: str, max_tokens: int = 1500) -> str:
    return generate_chat(system, [{"role": "user", "content": user}], max_tokens=max_tokens)
