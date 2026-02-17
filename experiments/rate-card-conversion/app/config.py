from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Rate Card Conversion"
    api_prefix: str = "/v1"
    confidence_threshold: float = 0.80
    use_llm_mapping: bool = False
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="RCC_")


settings = Settings()
