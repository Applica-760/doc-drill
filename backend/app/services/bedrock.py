import base64
import json
import logging

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.models.document import Document
from app.services import s3

logger = logging.getLogger(__name__)


def make_bedrock_client(service: str) -> boto3.client:
    """Bedrock 系サービス用の boto3 クライアントを生成する。

    docker-compose では AWS_ACCESS_KEY_ID が MinIO 認証情報に上書きされるため、
    Bedrock には BEDROCK_AWS_ACCESS_KEY_ID を別途指定する。
    AWS デプロイ時はこれらが空文字になり、boto3 が IAM タスクロールを自動使用する。
    """
    kwargs: dict = {"region_name": settings.aws_default_region}
    if settings.bedrock_aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.bedrock_aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.bedrock_aws_secret_access_key
    return boto3.client(service, **kwargs)


_SYSTEM_PROMPT = (
    "あなたは教育コンテンツの作成アシスタントです。"
    "指示に従い、必ず有効なJSON配列のみを返してください。前置きや説明文は一切不要です。"
)

_USER_PROMPT_TEMPLATE = """\
以下の資料を読み、短答式の問題を{count}問作成してください。

以下のJSON配列形式のみで回答してください。

[
  {{
    "body": "問題文（具体的な短答形式の問い）",
    "answer": "正解（簡潔に）",
    "explanation": "解説（なぜその答えなのか、背景知識も含めて説明）"
  }}
]
"""


def _parse_questions(raw: str) -> list[dict]:
    """Claude のレスポンスから JSON 配列を抽出してパースする。"""
    text = raw.strip()
    # コードブロック（```json ... ```）が含まれる場合に除去
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def generate_questions(document: Document, count: int) -> list[dict]:
    """Bedrock Claude を呼び出して短答式問題を生成する。

    KB 有効時（本番）: Bedrock Knowledge Bases から関連チャンクを取得しコンテキストとして渡す。
    KB 無効時（ローカル）: S3/MinIO から PDF を直接取得して Claude に送信する。
    """
    if settings.bedrock_kb_enabled:
        return _generate_with_kb(document, count)
    else:
        return _generate_with_pdf(document, count)


def _generate_with_pdf(document: Document, count: int) -> list[dict]:
    """PDF を直接 Claude に送信して問題を生成する（KB 無効時 / ローカル開発用）。

    ローカル環境では KB が存在しないため、MinIO から PDF を取得して
    Claude のドキュメント入力として直接渡す。
    AWS デプロイ後は _generate_with_kb に切り替わる。
    """
    pdf_bytes = s3.get_file_bytes(document.s3_key)
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode()

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": _SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": _USER_PROMPT_TEMPLATE.format(count=count),
                    },
                ],
            }
        ],
    })

    return _invoke_model(body)


def _generate_with_kb(document: Document, count: int) -> list[dict]:
    """Bedrock Knowledge Base から関連チャンクを取得して問題を生成する（KB 有効時 / 本番用）。

    ローカル開発では bedrock_kb_enabled=false のためこのパスは通らない。
    """
    bedrock_agent_runtime = make_bedrock_client("bedrock-agent-runtime")

    try:
        retrieve_response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=settings.bedrock_kb_id,
            retrievalQuery={"text": "この資料の重要な概念・用語・事実"},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": 10}
            },
        )
        contexts = [
            r["content"]["text"]
            for r in retrieve_response.get("retrievalResults", [])
        ]
    except ClientError as e:
        logger.warning("KB retrieval failed: %s", e.response["Error"]["Message"])
        contexts = []

    context_text = "\n\n".join(contexts) if contexts else "（資料の取得に失敗しました）"

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": _SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"以下は資料から抜粋したテキストです。\n\n{context_text}",
                    },
                    {
                        "type": "text",
                        "text": _USER_PROMPT_TEMPLATE.format(count=count),
                    },
                ],
            }
        ],
    })

    return _invoke_model(body)


def _invoke_model(body: str) -> list[dict]:
    bedrock_runtime = make_bedrock_client("bedrock-runtime")

    try:
        response = bedrock_runtime.invoke_model(
            modelId=settings.bedrock_model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        raw = json.loads(response["body"].read())["content"][0]["text"]
        return _parse_questions(raw)
    except ClientError as e:
        raise RuntimeError(
            f"Bedrock invoke_model failed: {e.response['Error']['Message']}"
        ) from e
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise RuntimeError(f"Failed to parse Bedrock response: {e}") from e
