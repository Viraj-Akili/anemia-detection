from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based application configuration.

    Values are read from environment variables (e.g. DATABASE_URL) or from
    a local .env file if present. See backend/.env.example for the template.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://user:password@localhost:5432/prahari"
    environment: str = "development"
    debug: bool = True


settings = Settings()
