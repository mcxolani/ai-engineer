from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    classifier_provider: Literal["demo", "openai"] = "demo"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o-mini"

    @model_validator(mode="after")
    def require_api_key(self):
        if (
            self.classifier_provider == "openai"
            and not self.openai_api_key.get_secret_value().strip()
        ):
            raise ValueError("Set OPENAI_API_KEY in .env when CLASSIFIER_PROVIDER=openai")
        return self
