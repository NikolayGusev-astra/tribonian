"""CLI entry-point for the Google Drive Folder Summarizer."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from gdrive_summarizer.config import DOWNLOAD_DIR, OPENROUTER_API_KEY
from gdrive_summarizer.summarizer import summarize_folder


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Скачивает файлы из публичной папки Google Drive и генерирует общее саммари.",
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL публичной Google Drive папки",
    )
    parser.add_argument(
        "--output",
        default=DOWNLOAD_DIR,
        help=f"Директория для скачанных файлов (по умолчанию: {DOWNLOAD_DIR})",
    )
    parser.add_argument(
        "--save",
        default="summary.txt",
        help="Файл для сохранения итогового саммари (по умолчанию: summary.txt)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод (DEBUG-уровень логирования)",
    )
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    # Validate API key early
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("sk-or-v1-xxx"):
        print(
            "ОШИБКА: Установите OPENROUTER_API_KEY в файле .env\n"
            "  Получить ключ: https://openrouter.ai/keys",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run the pipeline
    summary = summarize_folder(folder_url=args.url, output_dir=args.output)

    # Print to console
    print("\n" + "=" * 60)
    print("ИТОГОВОЕ САММАРИ ПАПКИ")
    print("=" * 60)
    print(summary)
    print("=" * 60)

    # Save to file
    save_path = Path(args.save)
    save_path.write_text(summary, encoding="utf-8")
    print(f"\nСаммари сохранено в: {save_path.resolve()}")


if __name__ == "__main__":
    main()
