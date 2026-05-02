import json
import logging

from app.services.bedrock import make_bedrock_client

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
_DIMENSIONS = 1024


def embed(text: str) -> list[float]:
    """テキストを Bedrock Titan Embed v2 でベクトル化する（1024次元）。"""
    client = make_bedrock_client("bedrock-runtime")
    body = json.dumps({"inputText": text, "dimensions": _DIMENSIONS})
    response = client.invoke_model(
        modelId=_EMBEDDING_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(response["body"].read())["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """複数テキストを順に埋め込む（Titan v2 はバッチAPIなし）。"""
    return [embed(t) for t in texts]
