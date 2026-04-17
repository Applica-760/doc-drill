import uuid
from io import BytesIO

from app.dependencies.user import MVP_USER_ID


def _upload(client, filename: str = "test.pdf") -> dict:
    """ヘルパー: ダミー PDF をアップロードしてレスポンス JSON を返す。"""
    files = {"file": (filename, BytesIO(b"%PDF-1.4 dummy"), "application/pdf")}
    response = client.post("/documents", files=files)
    assert response.status_code == 201
    return response.json()


# ── POST /documents ───────────────────────────────────────────────────────────


def test_upload_document_success(client, mock_s3, mock_kb_ingest):
    data = _upload(client)

    assert data["file_name"] == "test.pdf"
    assert data["user_id"] == str(MVP_USER_ID)
    assert data["kb_document_id"] is None
    mock_s3.upload_fileobj.assert_called_once()
    mock_kb_ingest.assert_called_once()


# ── GET /documents ────────────────────────────────────────────────────────────


def test_list_documents(client, mock_s3, mock_kb_ingest):
    _upload(client, "a.pdf")
    _upload(client, "b.pdf")

    response = client.get("/documents")

    assert response.status_code == 200
    assert len(response.json()) == 2


# ── DELETE /documents/{id} ────────────────────────────────────────────────────


def test_delete_document_success(client, mock_s3, mock_kb_ingest):
    doc_id = _upload(client)["id"]

    response = client.delete(f"/documents/{doc_id}")

    assert response.status_code == 204
    mock_s3.delete_object.assert_called_once()

    # 削除後は一覧から消えている
    remaining = client.get("/documents").json()
    assert all(d["id"] != doc_id for d in remaining)


def test_delete_document_not_found(client):
    response = client.delete(f"/documents/{uuid.uuid4()}")
    assert response.status_code == 404
