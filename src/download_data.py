"""Download the official UCI Online Retail workbook."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

import requests


DATASET_URL = (
    "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
)
EXPECTED_WORKBOOK = "Online Retail.xlsx"


def download(destination: Path, timeout: int = 120) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / "online_retail.zip"
    workbook_path = destination / "online_retail.xlsx"

    with requests.get(DATASET_URL, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with archive_path.open("wb") as archive:
            shutil.copyfileobj(response.raw, archive)

    if not zipfile.is_zipfile(archive_path):
        raise ValueError("Downloaded file is not a valid ZIP archive.")

    with zipfile.ZipFile(archive_path) as archive:
        members = archive.namelist()
        if EXPECTED_WORKBOOK not in members:
            raise ValueError(
                f"Expected {EXPECTED_WORKBOOK!r}; archive contains {members}."
            )
        with archive.open(EXPECTED_WORKBOOK) as source, workbook_path.open("wb") as target:
            shutil.copyfileobj(source, target)

    archive_path.unlink()
    print(f"Downloaded dataset to {workbook_path}")
    return workbook_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download UCI Online Retail data.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    download(arguments.destination)
