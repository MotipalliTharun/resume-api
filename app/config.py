from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"

    database_url: str = "postgresql://resume:resume@db:5432/resumeai"
    
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_model: str = "gpt-4o-mini"
    
    # Auth
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Change in prod!
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()
