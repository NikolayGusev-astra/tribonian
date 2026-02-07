"""Orchestrator: download files, extract content, produce a combined summary."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from gdrive_summarizer import llm_client
from gdrive_summarizer.downloader import download_folder

# Importing processor modules triggers their self-registration.
from gdrive_summarizer.processors import base as _base  # noqa: F401
from gdrive_summarizer.processors import image_processor as _img  # noqa: F401
from gdrive_summarizer.processors import pdf_processor as _pdf  # noqa: F401
from gdrive_summarizer.processors import text_processor as _txt  # noqa: F401
from gdrive_summarizer.processors.base import get_processor

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert analyst. The user will give you descriptions / extracted "
    "content of several files from one folder. Produce a coherent, well-structured "
    "summary that covers ALL of the files. Highlight key themes, relationships "
    "between files, and any notable details. Answer in Russian."
)


def _extract_file_content(file_path: Path) -> Optional[str]:
    """Run the appropriate processor for a single file."""
    processor = get_processor(file_path)
    if processor is None:
        return None
    try:
        return processor.extract(file_path)
    except Exception:
        logger.exception("Failed to process %s", file_path.name)
        return None


def summarize_folder(
    folder_url: str,
    output_dir: str | None = None,
) -> str:
    """End-to-end pipeline: download → extract → summarise.

    Parameters
    ----------
    folder_url:
        Public Google Drive folder URL.
    output_dir:
        Where to store downloaded files.

    Returns
    -------
    str
        The final combined summary.
    """
    # Step 1: Download files
    files = download_folder(folder_url, output_dir)
    if not files:
        return "Папка пуста или файлы не удалось скачать."

    # Step 2: Extract / describe each file
    per_file: Dict[str, str] = {}
    for f in files:
        content = _extract_file_content(f)
        if content:
            per_file[f.name] = content
        else:
            per_file[f.name] = "(не удалось извлечь содержимое)"

    if not any(v != "(не удалось извлечь содержимое)" for v in per_file.values()):
        return "Не удалось извлечь содержимое ни из одного файла."

    # Step 3: Build a combined prompt with per-file content
    parts: List[str] = []
    for name, content in per_file.items():
        # Truncate very long content to stay within model context limits
        truncated = content[:12_000]
        if len(content) > 12_000:
            truncated += "\n... (содержимое обрезано)"
        parts.append(f"### Файл: {name}\n\n{truncated}")

    combined_prompt = (
        "Ниже приведено содержимое / описание каждого файла из папки.\n"
        "Сделай общее подробное саммари по ВСЕМ файлам папки.\n\n"
        + "\n\n---\n\n".join(parts)
    )

    # Step 4: Final LLM call for the combined summary
    logger.info("Generating final summary over %d file(s)…", len(per_file))
    summary = llm_client.chat(prompt=combined_prompt, system=_SYSTEM_PROMPT)
    return summary
