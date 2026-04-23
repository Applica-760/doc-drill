import boto3
from fastapi import UploadFile

from app.core.config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url or None,
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
    region_name=settings.aws_default_region,
)


def upload_file(file: UploadFile, key: str) -> None:
    _s3.upload_fileobj(file.file, settings.s3_bucket, key)


def delete_file(key: str) -> None:
    _s3.delete_object(Bucket=settings.s3_bucket, Key=key)


def get_file_bytes(key: str) -> bytes:
    response = _s3.get_object(Bucket=settings.s3_bucket, Key=key)
    return response["Body"].read()
