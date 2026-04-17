import logging

from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.bedrock import make_bedrock_client

logger = logging.getLogger(__name__)


def ingest_document(s3_key: str) -> str | None:
    """S3 上のドキュメントを Bedrock Knowledge Base に登録する。

    start_ingestion_job を呼び出すと、Bedrock がデータソース（S3）全体を
    非同期でスキャン・チャンキング・ベクトル化する。
    返り値の ingestionJobId を kb_document_id として DB に保存する。

    ローカル開発では bedrock_kb_enabled=false のためこの関数は呼ばれない。
    AWS デプロイ時のみ実際に KB への登録が行われる。
    """
    if not settings.bedrock_kb_enabled:
        return None

    try:
        response = make_bedrock_client("bedrock-agent").start_ingestion_job(
            knowledgeBaseId=settings.bedrock_kb_id,
            dataSourceId=settings.bedrock_kb_data_source_id,
        )
        job_id = response["ingestionJob"]["ingestionJobId"]
        logger.info("KB ingestion job started: job_id=%s s3_key=%s", job_id, s3_key)
        return job_id
    except ClientError as e:
        logger.warning(
            "KB ingestion job failed (s3_key=%s): %s",
            s3_key,
            e.response["Error"]["Message"],
        )
        return None
