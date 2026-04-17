import uuid
from io import BytesIO

import pytest


_BEDROCK_RETURN = [
    {"body": "Q1", "answer": "A1", "explanation": "E1"},
    {"body": "Q2", "answer": "A2", "explanation": "E2"},
]


@pytest.fixture
def mock_bedrock_generate(mocker):
    return mocker.patch(
        "app.services.bedrock.generate_questions",
        return_value=_BEDROCK_RETURN,
    )


@pytest.fixture
def uploaded_doc_id(client, mock_s3, mock_kb_ingest) -> str:
    """テスト用のドキュメントをアップロードして ID を返す。"""
    files = {"file": ("test.pdf", BytesIO(b"%PDF-1.4 dummy"), "application/pdf")}
    response = client.post("/documents", files=files)
    assert response.status_code == 201
    return response.json()["id"]


# ── POST /questions/generate ──────────────────────────────────────────────────


def test_generate_questions_success(client, uploaded_doc_id, mock_bedrock_generate):
    payload = {"document_id": uploaded_doc_id, "count": 2}
    response = client.post("/questions/generate", json=payload)

    assert response.status_code == 201
    questions = response.json()
    assert len(questions) == 2
    assert questions[0]["body"] == "Q1"
    assert questions[0]["question_type"] == "short_answer"
    mock_bedrock_generate.assert_called_once()


def test_generate_questions_document_not_found(client):
    payload = {"document_id": str(uuid.uuid4()), "count": 2}
    response = client.post("/questions/generate", json=payload)

    assert response.status_code == 404


def test_generate_questions_bedrock_error(client, uploaded_doc_id, mocker):
    mocker.patch(
        "app.services.bedrock.generate_questions",
        side_effect=RuntimeError("Bedrock invoke_model failed: service error"),
    )
    payload = {"document_id": uploaded_doc_id, "count": 2}
    response = client.post("/questions/generate", json=payload)

    assert response.status_code == 500


# ── GET /questions ────────────────────────────────────────────────────────────


def test_list_questions_all(client, uploaded_doc_id, mock_bedrock_generate):
    client.post("/questions/generate", json={"document_id": uploaded_doc_id, "count": 2})

    response = client.get("/questions")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_questions_filtered_by_document_id(
    client, uploaded_doc_id, mock_bedrock_generate, mock_s3, mock_kb_ingest
):
    # 1 件目のドキュメントに問題を生成
    client.post("/questions/generate", json={"document_id": uploaded_doc_id, "count": 2})

    # 2 件目のドキュメントをアップロードして問題を生成
    files = {"file": ("other.pdf", BytesIO(b"%PDF-1.4"), "application/pdf")}
    other_doc_id = client.post("/documents", files=files).json()["id"]
    client.post("/questions/generate", json={"document_id": other_doc_id, "count": 2})

    # 1 件目のみでフィルタ
    response = client.get(f"/questions?document_id={uploaded_doc_id}")

    assert response.status_code == 200
    questions = response.json()
    assert len(questions) == 2
    assert all(q["document_id"] == uploaded_doc_id for q in questions)


# ── GET /questions/{id} ───────────────────────────────────────────────────────


def test_get_question_success(client, uploaded_doc_id, mock_bedrock_generate):
    questions = client.post(
        "/questions/generate",
        json={"document_id": uploaded_doc_id, "count": 2},
    ).json()
    question_id = questions[0]["id"]

    response = client.get(f"/questions/{question_id}")

    assert response.status_code == 200
    assert response.json()["id"] == question_id


def test_get_question_not_found(client):
    response = client.get(f"/questions/{uuid.uuid4()}")
    assert response.status_code == 404
