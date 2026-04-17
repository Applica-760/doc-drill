import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

import app.services.bedrock as bedrock_module
from app.services.bedrock import _parse_questions, generate_questions


# ── _parse_questions ──────────────────────────────────────────────────────────


def test_parse_questions_plain_json():
    raw = '[{"body": "Q1", "answer": "A1", "explanation": "E1"}]'
    result = _parse_questions(raw)
    assert result == [{"body": "Q1", "answer": "A1", "explanation": "E1"}]


def test_parse_questions_with_code_block():
    raw = '```json\n[{"body": "Q1", "answer": "A1", "explanation": "E1"}]\n```'
    result = _parse_questions(raw)
    assert result == [{"body": "Q1", "answer": "A1", "explanation": "E1"}]


def test_parse_questions_invalid_json_raises():
    with pytest.raises((json.JSONDecodeError, ValueError)):
        _parse_questions("not valid json at all")


# ── generate_questions のルーティング ─────────────────────────────────────────


def test_generate_questions_routes_to_pdf_when_kb_disabled(mocker):
    mock_pdf = mocker.patch(
        "app.services.bedrock._generate_with_pdf", return_value=[]
    )
    mocker.patch.object(bedrock_module.settings, "bedrock_kb_enabled", new=False)

    doc = MagicMock()
    generate_questions(doc, 3)

    mock_pdf.assert_called_once_with(doc, 3)


def test_generate_questions_routes_to_kb_when_kb_enabled(mocker):
    mock_kb = mocker.patch(
        "app.services.bedrock._generate_with_kb", return_value=[]
    )
    mocker.patch.object(bedrock_module.settings, "bedrock_kb_enabled", new=True)

    doc = MagicMock()
    generate_questions(doc, 3)

    mock_kb.assert_called_once_with(doc, 3)


# ── _generate_with_pdf ────────────────────────────────────────────────────────


def _make_bedrock_response(questions: list[dict]) -> MagicMock:
    """Bedrock invoke_model のレスポンス形式を模倣した Mock を返す。"""
    body_content = json.dumps({"content": [{"text": json.dumps(questions)}]})
    mock_body = MagicMock()
    mock_body.read.return_value = body_content.encode()
    return {"body": mock_body}


def test_generate_with_pdf_calls_bedrock(mocker):
    mocker.patch(
        "app.services.bedrock.s3.get_file_bytes",
        return_value=b"%PDF-1.4 dummy",
    )
    expected = [{"body": "Q", "answer": "A", "explanation": "E"}]
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = _make_bedrock_response(expected)
    mocker.patch(
        "app.services.bedrock.make_bedrock_client", return_value=mock_client
    )

    doc = MagicMock()
    doc.s3_key = "documents/test/test.pdf"

    result = bedrock_module._generate_with_pdf(doc, 1)

    assert result == expected
    mock_client.invoke_model.assert_called_once()


# ── _generate_with_kb ─────────────────────────────────────────────────────────


def test_generate_with_kb_calls_retrieve_then_model(mocker):
    expected = [{"body": "Q", "answer": "A", "explanation": "E"}]
    mock_client = MagicMock()
    mock_client.retrieve.return_value = {
        "retrievalResults": [{"content": {"text": "some context"}}]
    }
    mock_client.invoke_model.return_value = _make_bedrock_response(expected)
    mocker.patch(
        "app.services.bedrock.make_bedrock_client", return_value=mock_client
    )

    result = bedrock_module._generate_with_kb(MagicMock(), 1)

    mock_client.retrieve.assert_called_once()
    mock_client.invoke_model.assert_called_once()
    assert result == expected


def test_generate_with_kb_handles_retrieve_failure(mocker):
    """KB retrieve が失敗してもフォールバックして invoke_model を呼ぶ。"""
    expected = [{"body": "Q", "answer": "A", "explanation": "E"}]
    mock_client = MagicMock()
    error_response = {
        "Error": {"Code": "ResourceNotFoundException", "Message": "KB not found"}
    }
    mock_client.retrieve.side_effect = ClientError(error_response, "Retrieve")
    mock_client.invoke_model.return_value = _make_bedrock_response(expected)
    mocker.patch(
        "app.services.bedrock.make_bedrock_client", return_value=mock_client
    )

    result = bedrock_module._generate_with_kb(MagicMock(), 1)

    # retrieve 失敗後もフォールバックして invoke_model が呼ばれ結果が返る
    mock_client.invoke_model.assert_called_once()
    assert result == expected
