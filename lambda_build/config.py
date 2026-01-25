from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"

    database_url: str = "postgresql://resume:resume@db:5432/resumeai"
    
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    app_password_hash: str | None = "$2b$12$oYW1z3kw0xRtcZFhqWtOqeQuPN.Na/pZccFR3I5EFLGYNgcUVb2ma"

settings = Settings()
