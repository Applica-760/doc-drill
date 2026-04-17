from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    database_url: str
    s3_endpoint_url: str
    s3_bucket: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str = "ap-northeast-1"

    # Bedrock Knowledge Bases
    # ローカル開発では false にして KB 登録をスキップする。
    # AWS デプロイ時は true に設定し、kb_id / kb_data_source_id も必須。
    bedrock_kb_enabled: bool = False
    bedrock_kb_id: str = ""
    bedrock_kb_data_source_id: str = ""

    # Bedrock Claude 呼び出し用モデルID
    # ap-northeast-1 では cross-region inference profile 経由が必須。
    # "jp." プレフィックスが日本リージョン向けプロファイルの識別子。
    bedrock_model_id: str = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # Bedrock 用 AWS 認証情報（ローカル開発専用）
    # docker-compose では AWS_ACCESS_KEY_ID が MinIO 認証情報に上書きされるため、
    # Bedrock には別途専用の認証情報を渡す必要がある。
    # AWS デプロイ時は IAM タスクロールで解決されるため、これらの設定は不要。
    bedrock_aws_access_key_id: str = ""
    bedrock_aws_secret_access_key: str = ""


settings = Settings()
