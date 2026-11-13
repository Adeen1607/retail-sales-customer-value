"""Download the official UCI Online Retail workbook."""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import requests


DATASET_URL = (
    "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
)
EXPECTED_WORKBOOK = "Online Retail.xlsx"
MAX_WORKBOOK_BYTES = 100 * 1024 * 1024


def download(destination: Path, timeout: int = 120) -> Path:
    """Download to temporary files and never replace an existing workbook."""
    destination.mkdir(parents=True, exist_ok=True)
    workbook_path = destination / "online_retail.xlsx"
    if workbook_path.exists():
        raise FileExistsError(f"Workbook already exists: {workbook_path}")

    archive_path = None
    staged_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".retail_", suffix=".zip", dir=destination, delete=False
        ) as archive_file:
            archive_path = Path(archive_file.name)
            with requests.get(DATASET_URL, stream=True, timeout=timeout) as response:
                response.raise_for_status()
                shutil.copyfileobj(response.raw, archive_file)

        if not zipfile.is_zipfile(archive_path):
            raise ValueError("Downloaded file is not a valid ZIP archive.")

        with zipfile.ZipFile(archive_path) as archive:
            try:
                info = archive.getinfo(EXPECTED_WORKBOOK)
            except KeyError as exc:
                raise ValueError(
                    f"Expected {EXPECTED_WORKBOOK!r} in downloaded archive."
                ) from exc
            if info.is_dir() or info.file_size > MAX_WORKBOOK_BYTES:
                raise ValueError("Workbook entry is invalid or exceeds the size limit.")
            with tempfile.NamedTemporaryFile(
                prefix=".retail_", suffix=".xlsx", dir=destination, delete=False
            ) as staged_file:
                staged_path = Path(staged_file.name)
                with archive.open(info) as source:
                    shutil.copyfileobj(source, staged_file)
            if staged_path.stat().st_size != info.file_size:
                raise ValueError("Extracted workbook size does not match ZIP metadata.")

        # Hard-link creation is atomic and fails if another process created the file.
        os.link(staged_path, workbook_path)
    finally:
        if archive_path is not None:
            archive_path.unlink(missing_ok=True)
        if staged_path is not None:
            staged_path.unlink(missing_ok=True)

    print(f"Downloaded dataset to {workbook_path}")
    return workbook_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download UCI Online Retail data.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    download(arguments.destination)
