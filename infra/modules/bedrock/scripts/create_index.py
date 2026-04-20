#!/usr/bin/env python3
"""
OpenSearch Serverless にベクターインデックスを作成する。
Bedrock Knowledge Bases はインデックスが事前に存在することを要求するため、
terraform apply 中の null_resource から呼び出される。

依存: boto3（標準の Python 環境に含まれる想定）
環境変数: AOSS_ENDPOINT, AWS_REGION, INDEX_NAME
"""

import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

import boto3


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k = _sign(k, region)
    k = _sign(k, service)
    return _sign(k, "aws4_request")


def _signed_request(
    method: str,
    url: str,
    region: str,
    body: str,
    credentials,
) -> urllib.request.Request:
    parsed      = urlparse(url)
    host        = parsed.netloc
    uri         = parsed.path or "/"
    service     = "aoss"
    payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    now        = datetime.now(timezone.utc)
    amz_date   = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    headers = {
        "content-type": "application/json",
        "host":         host,
        "x-amz-date":  amz_date,
    }
    if credentials.token:
        headers["x-amz-security-token"] = credentials.token

    signed_headers    = ";".join(sorted(headers.keys()))
    canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted(headers.items()))

    canonical_request = "\n".join([
        method, uri, "",
        canonical_headers, signed_headers, payload_hash,
    ])

    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign   = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    sig = hmac.new(
        _signing_key(credentials.secret_key, date_stamp, region, service),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    auth = (
        f"AWS4-HMAC-SHA256 Credential={credentials.access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={sig}"
    )

    req_headers = {k: v for k, v in headers.items() if k != "host"}
    req_headers["Authorization"] = auth

    return urllib.request.Request(
        url, data=body.encode("utf-8"), headers=req_headers, method=method
    )


def main() -> None:
    endpoint   = os.environ["AOSS_ENDPOINT"]
    region     = os.environ["AWS_REGION"]
    index_name = os.environ["INDEX_NAME"]

    if not endpoint.startswith("https://"):
        endpoint = "https://" + endpoint

    credentials = boto3.Session().get_credentials().get_frozen_credentials()

    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512,
            }
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type":      "knn_vector",
                    "dimension": 1024,
                    "method": {
                        "name":       "hnsw",
                        "engine":     "faiss",
                        "parameters": {"m": 16, "ef_construction": 512},
                        "space_type": "l2",
                    },
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text", "index": "true"},
                "AMAZON_BEDROCK_METADATA":   {"type": "text", "index": "false"},
            }
        },
    }

    url     = f"{endpoint}/{index_name}"
    payload = json.dumps(index_body)
    req     = _signed_request("PUT", url, region, payload, credentials)

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Index created: {resp.status} {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        if "resource_already_exists_exception" in body_text.lower():
            print("Index already exists, skipping")
        else:
            print(f"Failed to create index: {e.code} {body_text}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
