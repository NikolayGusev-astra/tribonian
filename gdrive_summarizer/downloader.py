"""Download all files from a public Google Drive folder using *gdown*."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import gdown

from gdrive_summarizer.config import DOWNLOAD_DIR

logger = logging.getLogger(__name__)


def download_folder(
    folder_url: str,
    output_dir: str | None = None,
) -> List[Path]:
    """Download every file from a public Google Drive folder.

    Parameters
    ----------
    folder_url:
        Full URL of the shared Google Drive folder.
    output_dir:
        Local directory to save files into.  Defaults to ``DOWNLOAD_DIR``.

    Returns
    -------
    List[Path]
        Sorted list of paths to the downloaded files.
    """
    dest = Path(output_dir or DOWNLOAD_DIR)
    dest.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading folder %s -> %s", folder_url, dest)

    # gdown.download_folder returns a list of file paths (str)
    downloaded: list[str] = gdown.download_folder(
        url=folder_url,
        output=str(dest),
        quiet=False,
    )

    if not downloaded:
        logger.warning("No files were downloaded from %s", folder_url)
        return []

    paths = sorted(Path(p) for p in downloaded)
    logger.info("Downloaded %d file(s): %s", len(paths), [p.name for p in paths])
    return paths
