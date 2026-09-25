"""
Client LLM unifié — OpenAI (GPT-4o-mini) ou Gemini Flash.

Aucun chiffre n'est inventé ici : l'appelant fournit le contexte.
Timeout court (hackathon / réseau instable). En cas d'échec, l'appelant
gère le fallback (parseur SMS, règles TresorIA, erreur explicite).
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Optional


def _setting(name: str, default: str = "") -> str:
    try:
        from django.conf import settings

        val = getattr(settings, name, None)
        if val:
            return str(val)
    except Exception:
        pass
    return os.environ.get(name, default) or default


def openai_api_key() -> str:
    return _setting("OPENAI_API_KEY").strip()


def gemini_api_key() -> str:
    return _setting("GEMINI_API_KEY").strip()


def llm_configured() -> bool:
    if mock_fallback_enabled():
        return False
    return bool(openai_api_key() or gemini_api_key())


def mock_fallback_enabled() -> bool:
    """Autorisé uniquement pour pytest — jamais le chemin prod par défaut."""
    env = os.environ.get("MONEXA_AI_FALLBACK_MOCK", "")
    if str(env).lower() in ("1", "true", "yes"):
        return True
    raw = _setting("MONEXA_AI_FALLBACK_MOCK", "")
    return str(raw).lower() in ("1", "true", "yes")


def _http_json(url: str, payload: dict, headers: dict, timeout: int = 20) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc


def _extract_json_object(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Réponse LLM sans objet JSON.")
    return json.loads(text[start : end + 1])


def _guess_mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"GIF8"):
        return "image/gif"
    if image_bytes.startswith(b"%PDF"):
        return "application/pdf"
    return "image/jpeg"


def chat_complete(
    *,
    system: str,
    user: str,
    image_bytes: Optional[bytes] = None,
    json_mode: bool = True,
    timeout: int = 20,
) -> str:
    """
    Appel texte (+ image optionnelle). Préfère OpenAI si les deux clés sont présentes.
    """
    if openai_api_key():
        return _openai_complete(
            system=system,
            user=user,
            image_bytes=image_bytes,
            json_mode=json_mode,
            timeout=timeout,
        )
    if gemini_api_key():
        return _gemini_complete(
            system=system,
            user=user,
            image_bytes=image_bytes,
            json_mode=json_mode,
            timeout=timeout,
        )
    raise RuntimeError(
        "Aucune clé LLM. Définissez OPENAI_API_KEY ou GEMINI_API_KEY dans backend/.env."
    )


def chat_json(**kwargs) -> dict:
    raw = chat_complete(json_mode=True, **kwargs)
    return _extract_json_object(raw)


def _openai_complete(
    *,
    system: str,
    user: str,
    image_bytes: Optional[bytes],
    json_mode: bool,
    timeout: int,
) -> str:
    user_content: list | str
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        mime = _guess_mime(image_bytes)
        user_content = [
            {"type": "text", "text": user},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            },
        ]
    else:
        user_content = user

    payload: dict = {
        "model": os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    data = _http_json(
        "https://api.openai.com/v1/chat/completions",
        payload,
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key()}",
        },
        timeout=timeout,
    )
    return data["choices"][0]["message"]["content"]


def _gemini_complete(
    *,
    system: str,
    user: str,
    image_bytes: Optional[bytes],
    json_mode: bool,
    timeout: int,
) -> str:
    parts: list = [{"text": f"{system}\n\n{user}"}]
    if image_bytes:
        parts.append(
            {
                "inline_data": {
                    "mime_type": _guess_mime(image_bytes),
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                }
            }
        )
    gen_cfg: dict = {"temperature": 0}
    if json_mode:
        gen_cfg["responseMimeType"] = "application/json"

    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    key = gemini_api_key()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    data = _http_json(
        url,
        {"contents": [{"parts": parts}], "generationConfig": gen_cfg},
        {"Content-Type": "application/json"},
        timeout=timeout,
    )
    return data["candidates"][0]["content"]["parts"][0]["text"]
