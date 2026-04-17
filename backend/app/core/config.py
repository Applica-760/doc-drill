from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    s3_endpoint_url: str
    s3_bucket: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str = "ap-northeast-1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
