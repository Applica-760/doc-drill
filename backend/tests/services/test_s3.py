from io import BytesIO
from unittest.mock import MagicMock

import app.services.s3 as s3_module
from app.core.config import settings
from app.services.s3 import delete_file, get_file_bytes, upload_file


# ── fixtures ──────────────────────────────────────────────────────────────────
# conftest の mock_s3 は routers テスト向けの汎用 fixture。
# services テストでは boto3 メソッドの呼び出し引数を細かく検証したいため
# ここでシンプルな patch を使う。


def test_upload_file(mocker):
    mock_client = mocker.MagicMock()
    mocker.patch.object(s3_module, "_s3", mock_client)

    file_obj = MagicMock()
    file_obj.file = BytesIO(b"dummy content")

    upload_file(file_obj, "documents/test.pdf")

    mock_client.upload_fileobj.assert_called_once_with(
        file_obj.file,
        settings.s3_bucket,
        "documents/test.pdf",
    )


def test_delete_file(mocker):
    mock_client = mocker.MagicMock()
    mocker.patch.object(s3_module, "_s3", mock_client)

    delete_file("documents/test.pdf")

    mock_client.delete_object.assert_called_once_with(
        Bucket=settings.s3_bucket,
        Key="documents/test.pdf",
    )


def test_get_file_bytes_returns_content(mocker):
    mock_client = mocker.MagicMock()
    mocker.patch.object(s3_module, "_s3", mock_client)
    expected = b"%PDF-1.4 dummy"
    mock_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=expected))
    }

    result = get_file_bytes("documents/test.pdf")

    assert result == expected
    mock_client.get_object.assert_called_once_with(
        Bucket=settings.s3_bucket,
        Key="documents/test.pdf",
    )
