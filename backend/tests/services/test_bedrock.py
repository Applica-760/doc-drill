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


# ── generate_questions ────────────────────────────────────────────────────────


def _make_bedrock_response(questions: list[dict]) -> MagicMock:
    body_content = json.dumps({"content": [{"text": json.dumps(questions)}]})
    mock_body = MagicMock()
    mock_body.read.return_value = body_content.encode()
    return {"body": mock_body}


def test_generate_questions_uses_vector_store_and_calls_model(mocker):
    expected = [{"body": "Q", "answer": "A", "explanation": "E"}]
    mocker.patch(
        "app.services.bedrock.vector_store.search",
        return_value=["chunk1", "chunk2"],
    )
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = _make_bedrock_response(expected)
    mocker.patch("app.services.bedrock.make_bedrock_client", return_value=mock_client)

    doc = MagicMock()
    db = MagicMock()
    result = generate_questions(doc, 1, db)

    bedrock_module.vector_store.search.assert_called_once()
    mock_client.invoke_model.assert_called_once()
    assert result == expected


def test_generate_questions_empty_chunks_still_calls_model(mocker):
    """チャンクが空でも invoke_model を呼び、結果を返す。"""
    expected = [{"body": "Q", "answer": "A", "explanation": "E"}]
    mocker.patch("app.services.bedrock.vector_store.search", return_value=[])
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = _make_bedrock_response(expected)
    mocker.patch("app.services.bedrock.make_bedrock_client", return_value=mock_client)

    result = generate_questions(MagicMock(), 1, MagicMock())

    mock_client.invoke_model.assert_called_once()
    assert result == expected


def test_invoke_model_raises_on_client_error(mocker):
    mocker.patch("app.services.bedrock.vector_store.search", return_value=[])
    mock_client = MagicMock()
    error_response = {"Error": {"Code": "ThrottlingException", "Message": "throttled"}}
    mock_client.invoke_model.side_effect = ClientError(error_response, "InvokeModel")
    mocker.patch("app.services.bedrock.make_bedrock_client", return_value=mock_client)

    with pytest.raises(RuntimeError, match="Bedrock invoke_model failed"):
        generate_questions(MagicMock(), 1, MagicMock())
