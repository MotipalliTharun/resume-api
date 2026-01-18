from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"

    database_url: str = "postgresql://resume:resume@db:5432/resumeai"
    
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

settings = Settings()
