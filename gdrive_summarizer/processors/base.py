"""Abstract base class for file processors and the processor registry."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Base class that every file-type processor must inherit from.

    Subclasses implement ``extract`` which returns a textual
    representation of the file's content (extracted text, image
    description, etc.).
    """

    @abstractmethod
    def extract(self, file_path: Path) -> str:
        """Return a textual representation of *file_path*'s content."""
        ...


# ── Processor registry ────────────────────────────────────────────────

# Maps lowercase file extensions (with dot) to processor classes.
_EXTENSION_MAP: Dict[str, Type[BaseProcessor]] = {}


def register_processor(extension: str, processor_cls: Type[BaseProcessor]) -> None:
    """Register *processor_cls* for the given file *extension*.

    Parameters
    ----------
    extension:
        File extension **with** leading dot, e.g. ``".pdf"``.
    processor_cls:
        A concrete ``BaseProcessor`` subclass.
    """
    ext = extension.lower()
    _EXTENSION_MAP[ext] = processor_cls
    logger.debug("Registered %s for extension '%s'", processor_cls.__name__, ext)


def get_processor(file_path: Path) -> BaseProcessor | None:
    """Return an instantiated processor for *file_path* based on its extension.

    Returns ``None`` when no processor is registered for the extension.
    """
    ext = file_path.suffix.lower()
    cls = _EXTENSION_MAP.get(ext)
    if cls is None:
        logger.warning("No processor registered for extension '%s' (%s)", ext, file_path.name)
        return None
    return cls()
