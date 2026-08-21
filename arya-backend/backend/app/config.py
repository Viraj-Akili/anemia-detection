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

    # ML & CV subsystem configuration defaults
    ai_model: str = "random_forest"
    confidence_threshold: float = 0.5
    quality_min_brightness: float = 30.0
    quality_max_brightness: float = 250.0
    quality_min_sharpness: float = 50.0
    quality_min_contrast: float = 10.0
    quality_min_tissue_fraction: float = 0.10
    quality_min_resolution: int = 16
    image_size: int = 224
    max_image_size: int = 4096
    device: str = "cpu"
    max_upload_size_mb: int = 15


settings = Settings()
