"""Processor for plain-text files — reads content directly."""

from __future__ import annotations

import logging
from pathlib import Path

from gdrive_summarizer.processors.base import BaseProcessor, register_processor

logger = logging.getLogger(__name__)


class TextProcessor(BaseProcessor):
    """Read a text-based file and return its content as-is."""

    ENCODINGS = ("utf-8", "cp1251", "latin-1")

    def extract(self, file_path: Path) -> str:
        logger.info("Reading text file: %s", file_path.name)

        for enc in self.ENCODINGS:
            try:
                text = file_path.read_text(encoding=enc)
                logger.info(
                    "Read %d chars from %s (encoding=%s)",
                    len(text),
                    file_path.name,
                    enc,
                )
                return text
            except (UnicodeDecodeError, ValueError):
                continue

        logger.error("Failed to decode %s with any known encoding", file_path.name)
        return ""


# Self-register for common text extensions
for _ext in (".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".log", ".rst"):
    register_processor(_ext, TextProcessor)
