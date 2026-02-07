"""Processor for image files — describes them via a vision LLM.

Before sending to the model the image is:
1. Converted to PNG (universal format support across all providers).
2. Optionally enhanced (sharpening + contrast) which helps with scanned documents.
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

from gdrive_summarizer.processors.base import BaseProcessor, register_processor

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency at module level.
_llm_client = None


def _get_llm_client():
    global _llm_client
    if _llm_client is None:
        from gdrive_summarizer import llm_client as _mod  # noqa: WPS433
        _llm_client = _mod
    return _llm_client


def _prepare_image(file_path: Path, enhance: bool = True) -> str:
    """Load image, optionally enhance, convert to PNG base64 data-URL.

    Parameters
    ----------
    file_path:
        Path to an image file (any format Pillow supports).
    enhance:
        If ``True``, apply sharpening and contrast boost — useful for scans.

    Returns
    -------
    str
        ``data:image/png;base64,...`` data-URL ready for the vision API.
    """
    img = Image.open(file_path).convert("RGB")
    logger.info(
        "Loaded image %s: %dx%d, original format=%s",
        file_path.name,
        img.width,
        img.height,
        img.format,
    )

    if enhance:
        # Sharpen to improve OCR readability on scans
        img = img.filter(ImageFilter.SHARPEN)
        # Slight contrast boost
        img = ImageEnhance.Contrast(img).enhance(1.3)
        logger.debug("Applied sharpening + contrast enhancement to %s", file_path.name)

    # Convert to PNG bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    logger.info(
        "Converted %s to PNG (%d KB base64)",
        file_path.name,
        len(b64) // 1024,
    )
    return f"data:image/png;base64,{b64}"


class ImageProcessor(BaseProcessor):
    """Send an image to a vision-capable LLM and return its description."""

    def extract(self, file_path: Path) -> str:
        logger.info("Describing image via vision model: %s", file_path.name)

        data_url = _prepare_image(file_path, enhance=True)

        client = _get_llm_client()
        description = client.describe_image(
            data_url=data_url,
            prompt=(
                "Это изображение — скорее всего скан или фотография документа/страницы. "
                "Качество может быть невысоким. "
                "1) Внимательно распознай и перепиши ВЕСЬ текст, который видишь на изображении. "
                "Если текст на русском языке — пиши на русском. "
                "2) Если текст нечитаем или отсутствует, опиши содержимое изображения максимально подробно. "
                "3) Укажи язык текста и общий тип документа (если возможно определить)."
            ),
        )
        logger.info("Got description (%d chars) for %s", len(description), file_path.name)
        return description


# Self-register for common image extensions
for _ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"):
    register_processor(_ext, ImageProcessor)
