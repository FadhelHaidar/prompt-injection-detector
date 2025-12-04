from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Prompt Injection Detector API"
    MODEL_ID: str = "protectai/deberta-v3-base-prompt-injection-v2"
    MODEL_SUBFOLDER: str = "onnx"
    SCORE_THRESHOLD: float = 0.7 
    MAX_LENGTH: int = 512

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),  # do not protect the "model_" namespace
    )


settings = Settings()