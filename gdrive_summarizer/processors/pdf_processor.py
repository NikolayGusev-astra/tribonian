"""Processor for PDF files — extracts text using PyPDF2."""

from __future__ import annotations

import logging
from pathlib import Path

from PyPDF2 import PdfReader

from gdrive_summarizer.processors.base import BaseProcessor, register_processor

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    """Extract plain text from a PDF document."""

    def extract(self, file_path: Path) -> str:
        logger.info("Extracting text from PDF: %s", file_path.name)
        reader = PdfReader(str(file_path))
        pages: list[str] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
        full_text = "\n\n".join(pages)
        logger.info(
            "Extracted %d page(s), %d chars from %s",
            len(pages),
            len(full_text),
            file_path.name,
        )
        return full_text


# Self-register for common PDF extensions
register_processor(".pdf", PDFProcessor)
