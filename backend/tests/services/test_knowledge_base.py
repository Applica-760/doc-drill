from unittest.mock import MagicMock

from botocore.exceptions import ClientError

import app.services.knowledge_base as kb_module
from app.services.knowledge_base import ingest_document


def test_ingest_document_returns_job_id_when_kb_enabled(mocker):
    mocker.patch.object(kb_module.settings, "bedrock_kb_enabled", new=True)
    mocker.patch.object(kb_module.settings, "bedrock_kb_id", new="kb-123")
    mocker.patch.object(
        kb_module.settings, "bedrock_kb_data_source_id", new="ds-456"
    )

    mock_client = MagicMock()
    mock_client.start_ingestion_job.return_value = {
        "ingestionJob": {"ingestionJobId": "job-789"}
    }
    mocker.patch(
        "app.services.knowledge_base.make_bedrock_client", return_value=mock_client
    )

    result = ingest_document("documents/test/test.pdf")

    assert result == "job-789"
    mock_client.start_ingestion_job.assert_called_once_with(
        knowledgeBaseId="kb-123",
        dataSourceId="ds-456",
    )


def test_ingest_document_returns_none_when_kb_disabled(mocker):
    mocker.patch.object(kb_module.settings, "bedrock_kb_enabled", new=False)

    result = ingest_document("documents/test/test.pdf")

    assert result is None


def test_ingest_document_returns_none_on_client_error(mocker):
    mocker.patch.object(kb_module.settings, "bedrock_kb_enabled", new=True)
    mocker.patch.object(kb_module.settings, "bedrock_kb_id", new="kb-123")
    mocker.patch.object(
        kb_module.settings, "bedrock_kb_data_source_id", new="ds-456"
    )

    mock_client = MagicMock()
    error_response = {
        "Error": {"Code": "ServiceException", "Message": "internal error"}
    }
    mock_client.start_ingestion_job.side_effect = ClientError(
        error_response, "StartIngestionJob"
    )
    mocker.patch(
        "app.services.knowledge_base.make_bedrock_client", return_value=mock_client
    )

    result = ingest_document("documents/test/test.pdf")

    # ClientError でクラッシュせず None を返す
    assert result is None
