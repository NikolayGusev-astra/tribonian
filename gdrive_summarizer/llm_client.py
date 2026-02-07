"""HTTP client for the OpenRouter API (OpenAI-compatible)."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from gdrive_summarizer.config import (
    MAX_RETRIES,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    RETRY_DELAY,
    TEXT_MODEL,
    VISION_FALLBACK_MODELS,
    VISION_MODEL,
)

logger = logging.getLogger(__name__)


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }


def _request_with_retry(payload: Dict[str, Any]) -> str:
    """Send a chat-completion request with exponential back-off on rate-limit errors."""
    last_resp = None
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(
            OPENROUTER_BASE_URL,
            headers=_headers(),
            json=payload,
            timeout=120,
        )
        last_resp = resp

        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices")
            if choices and choices[0].get("message", {}).get("content"):
                return choices[0]["message"]["content"]
            # Some models return an error inside a 200 response
            error_msg = data.get("error", {}).get("message", "")
            if error_msg:
                logger.warning("Model returned error in 200 body: %s", error_msg)

        if resp.status_code in (429, 402, 503):
            wait = RETRY_DELAY * attempt
            logger.warning(
                "Rate-limited (HTTP %d), retrying in %.1fs (attempt %d/%d)",
                resp.status_code,
                wait,
                attempt,
                MAX_RETRIES,
            )
            time.sleep(wait)
            continue

        # 403 = content blocked by provider — no point retrying same model
        if resp.status_code == 403:
            error_body = ""
            try:
                error_body = resp.json().get("error", {}).get("message", "")
            except Exception:
                error_body = resp.text[:300]
            raise ContentBlockedError(
                f"Model {payload.get('model')} returned 403: {error_body}"
            )

        # Unexpected error — raise immediately
        resp.raise_for_status()

    raise RuntimeError(
        f"OpenRouter request failed after {MAX_RETRIES} retries. "
        f"Last status: {last_resp.status_code if last_resp else '?'}, "
        f"body: {last_resp.text[:500] if last_resp else 'N/A'}"
    )


class ContentBlockedError(Exception):
    """Raised when a provider blocks the request (HTTP 403)."""


# ── Public helpers ────────────────────────────────────────────────────


def chat(prompt: str, system: str = "") -> str:
    """Send a text-only chat completion request.

    Parameters
    ----------
    prompt:
        User message content.
    system:
        Optional system message.

    Returns
    -------
    str
        The assistant's reply.
    """
    messages: List[Dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": TEXT_MODEL,
        "messages": messages,
    }

    logger.debug("LLM chat request (model=%s, prompt length=%d)", TEXT_MODEL, len(prompt))
    reply = _request_with_retry(payload)
    logger.debug("LLM chat reply length=%d", len(reply))
    return reply


def describe_image(data_url: str, prompt: str = "Describe this image in detail.") -> str:
    """Send an image (as a data-URL) to a vision model and get a description.

    Tries the primary ``VISION_MODEL`` first, then walks through
    ``VISION_FALLBACK_MODELS`` on 403 / rate-limit errors.

    Parameters
    ----------
    data_url:
        Base64-encoded image in ``data:<mime>;base64,...`` format.
    prompt:
        Text prompt sent alongside the image.

    Returns
    -------
    str
        The model's textual description of the image.
    """
    messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ],
        }
    ]

    # Build ordered list: primary model + fallbacks (deduplicated)
    models_to_try: List[str] = [VISION_MODEL]
    for fb in VISION_FALLBACK_MODELS:
        if fb not in models_to_try:
            models_to_try.append(fb)

    last_error: Optional[Exception] = None

    for model in models_to_try:
        payload = {"model": model, "messages": messages}
        logger.info("Vision request — trying model %s", model)
        try:
            reply = _request_with_retry(payload)
            logger.info("Vision reply from %s (%d chars)", model, len(reply))
            return reply
        except ContentBlockedError as exc:
            logger.warning("Model %s blocked the image: %s", model, exc)
            last_error = exc
            continue
        except RuntimeError as exc:
            # Exhausted retries (rate limit) — try next model
            logger.warning("Model %s exhausted retries: %s", model, exc)
            last_error = exc
            continue

    raise RuntimeError(
        f"All vision models failed. Last error: {last_error}"
    )
