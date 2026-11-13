"""Offline regressions for the UCI workbook downloader."""

import io
import zipfile
from unittest.mock import patch

import pytest

from src.download_data import EXPECTED_WORKBOOK, download


class FakeResponse:
    def __init__(self, payload):
        self.raw = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def raise_for_status(self):
        pass


def archive_bytes(name=EXPECTED_WORKBOOK, payload=b"sample workbook"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, payload)
    return buffer.getvalue()


def fake_get(payload):
    return patch("src.download_data.requests.get", return_value=FakeResponse(payload))


def test_download_creates_workbook_and_cleans_staging(tmp_path):
    with fake_get(archive_bytes()):
        result = download(tmp_path)
    assert result.read_bytes() == b"sample workbook"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["online_retail.xlsx"]


def test_existing_workbook_is_not_overwritten_or_downloaded(tmp_path):
    workbook = tmp_path / "online_retail.xlsx"
    workbook.write_bytes(b"important existing data")
    with patch("src.download_data.requests.get") as get:
        with pytest.raises(FileExistsError):
            download(tmp_path)
        get.assert_not_called()
    assert workbook.read_bytes() == b"important existing data"


@pytest.mark.parametrize("payload", [b"not a zip", archive_bytes("other.xlsx")])
def test_invalid_archives_leave_no_output(tmp_path, payload):
    with fake_get(payload):
        with pytest.raises(ValueError):
            download(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_oversized_workbook_rejected_without_extraction(tmp_path):
    with patch("src.download_data.MAX_WORKBOOK_BYTES", 3):
        with fake_get(archive_bytes(payload=b"too long")):
            with pytest.raises(ValueError, match="size limit"):
                download(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_failed_network_request_cleans_temporary_file(tmp_path):
    with patch("src.download_data.requests.get", side_effect=RuntimeError("network down")):
        with pytest.raises(RuntimeError, match="network down"):
            download(tmp_path)
    assert list(tmp_path.iterdir()) == []
