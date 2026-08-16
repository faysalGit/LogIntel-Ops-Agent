import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LogIntel-Ops-Agent"
    VECTOR_DB_PATH: str = os.path.join("data", "vector_store")
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    SPLUNK_API_URL: str = ""
    GMAIL_SENDER: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
