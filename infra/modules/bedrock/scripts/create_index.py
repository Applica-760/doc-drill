#!/usr/bin/env python3
"""
OpenSearch Serverless にベクターインデックスを作成する。
Bedrock Knowledge Bases はインデックスが事前に存在することを要求するため、
terraform apply 中の null_resource から呼び出される。

依存: boto3（botocore.auth.SigV4Auth で署名）
環境変数: AOSS_ENDPOINT, AWS_REGION, INDEX_NAME
"""

import hashlib
import http.client
import json
import os
import sys
import urllib.parse

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def _signed_request(
    method: str,
    url: str,
    region: str,
    body: bytes,
    credentials,
) -> tuple[dict, bytes]:
    sha256 = hashlib.sha256(body).hexdigest()
    aws_req = AWSRequest(
        method=method,
        url=url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-amz-content-sha256": sha256,
        },
    )
    SigV4Auth(credentials, "aoss", region).add_auth(aws_req)
    return dict(aws_req.headers), body


def main() -> None:
    endpoint   = os.environ["AOSS_ENDPOINT"]
    region     = os.environ["AWS_REGION"]
    index_name = os.environ["INDEX_NAME"]

    if not endpoint.startswith("https://"):
        endpoint = "https://" + endpoint

    credentials = boto3.Session().get_credentials()

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
    payload = json.dumps(index_body).encode("utf-8")
    headers, body = _signed_request("PUT", url, region, payload, credentials)

    parsed = urllib.parse.urlparse(url)
    conn   = http.client.HTTPSConnection(parsed.netloc)
    conn.request("PUT", parsed.path, body=body, headers=headers)
    resp      = conn.getresponse()
    resp_body = resp.read().decode()

    if resp.status in (200, 201):
        print(f"Index created: {resp.status} {resp_body}")
    elif "resource_already_exists_exception" in resp_body.lower():
        print("Index already exists, skipping")
    else:
        print(f"Failed to create index: {resp.status} {resp_body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
