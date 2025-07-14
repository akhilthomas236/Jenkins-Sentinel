from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Environment
    env: str = Field(default="development", description="Environment (development/production)")
    
    # Jenkins Settings
    jenkins_url: str = Field(..., description="Jenkins server URL")
    jenkins_user: str = Field(..., description="Jenkins username")
    jenkins_token: str = Field(..., description="Jenkins API token")
    
    # Database Settings
    database_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost/buildanalyzer",
        description="Database connection URL"
    )
    
    # AWS Settings
    aws_access_key_id: str = Field(..., description="AWS access key ID")
    aws_secret_access_key: str = Field(..., description="AWS secret access key")
    aws_region: str = Field(..., description="AWS region")
    bedrock_model_id: str = Field(..., description="Amazon Bedrock model ID")
    
    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")
    analysis_timeout: int = Field(default=300, description="Analysis timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    batch_size: int = Field(default=100, description="Batch size for processing")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    learning_enabled: bool = Field(default=True, description="Enable learning from builds")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
