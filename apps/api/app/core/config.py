from functools import cache
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Request
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.core.i18n import repo_messages_dir


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["dev", "staging", "prod", "test"] = "dev"
    # Root log level (env LOG_LEVEL). Independent of `environment`: DEBUG can log SQL/HTTP detail.
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    callmissed_api_key: SecretStr | None = None
    callmissed_base_url: str = "https://api.callmissed.com/v1"
    callmissed_resource_url: str = "https://api.callmissed.com/api/v1"
    callmissed_extraction_model: str = "kimi-k2.5"
    callmissed_explanation_model: str = "sarvam-105b"
    callmissed_stt_model: str = "saaras:v4"
    callmissed_tts_model: str = "bulbul:v3"
    # TTS speaker id (unverified until scripts/probe_stt_formats.py runs with --yes-spend).
    callmissed_tts_voice: str = "anushka"
    # packages/i18n/messages (spoken fallback answers). /app/i18n in the Docker image.
    i18n_messages_dir: Path = Field(default_factory=repo_messages_dir)
    supabase_url: str = ""
    supabase_project_ref: str = ""
    supabase_jwks_url: str = ""
    supabase_secret_key: SecretStr | None = None
    supabase_storage_bucket: str = "label-photos"
    # Private bucket for spoken answers (voice/{account_id}/{uuid}.mp3), kept at most 24 h.
    supabase_voice_bucket: str = "voice-answers"
    # POST /v1/voice/ask answers 503 `ai_unavailable` while false (Ruling V1 S3). Stays false
    # on dev and prod until the 24 h voice retention is live and the user approves the paid
    # STT/TTS probe (scripts/probe_stt_formats.py --yes-spend).
    voice_enabled: bool = False
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres"
    )
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    off_user_agent: str = "SmartNutri/0.1"
    off_base_url: str = "https://world.openfoodfacts.org"
    off_cache_ttl_hours: int = 168
    # Confidence passed to the engine for OFF data (crowd-sourced; < 1.0, >= 0.7 so allergen rules still run).
    off_data_confidence: float = 0.9
    rate_limit_label_scans_per_day: int = 30
    rate_limit_voice_per_day: int = 20
    rate_limit_reports_per_day: int = 10
    rate_limit_scan_uploads_per_day: int = 60
    rate_limit_label_requests_per_day: int = 200
    rate_limit_product_creates_per_day: int = 50
    rate_limit_analyze_per_hour: int = 120
    rate_limit_public_per_minute: int = 60
    rate_limit_meal_logs_per_day: int = 300
    rate_limit_search_per_minute: int = 60
    # One shared bucket for every authenticated route that may call Open Food Facts on a
    # cache miss: barcode lookup (Plan 8 Task 6), alternatives and compare (Plan 6).
    rate_limit_product_lookups_per_hour: int = 300
    # Trusted reverse-proxy hops in front of the API (see .env.example). 0 = use socket peer.
    trusted_proxy_hops: int = Field(default=0, ge=0)
    sentry_dsn: str | None = None
    posthog_api_key: str | None = None
    # Phone OTP via the Supabase Send-SMS hook -> CallMissed WhatsApp (Plan 8 Task 5). Stays
    # false until Meta approves the AUTHENTICATION template (Plan 8 Task 14).
    phone_otp_enabled: bool = False
    # "v1,whsec_<base64>" from Supabase -> Auth -> Hooks. SECRET.
    supabase_send_sms_hook_secret: SecretStr | None = None
    callmissed_whatsapp_otp_template: str = "smartnutri_otp"
    callmissed_whatsapp_phone_number_id: str = ""

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_level(cls, v: Any) -> Any:
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("allowed_origins")
    @classmethod
    def _no_wildcard(cls, v: list[str]) -> list[str]:
        if "*" in v:
            raise ValueError("allowed_origins must not contain '*'")
        return v

    @model_validator(mode="after")
    def _https_origins_in_prod(self) -> "Settings":
        if self.environment == "prod":
            bad = [o for o in self.allowed_origins if not o.startswith("https://")]
            if bad:
                raise ValueError("in prod, every allowed origin must be https://")
        return self


@cache
def get_settings() -> Settings:
    """Process settings from the environment (and apps/api/.env). Only `create_app()` with no
    arguments and Alembic use this; request-time code uses `get_app_settings`."""
    return Settings()


def get_app_settings(request: Request) -> Settings:
    """FastAPI dependency: the Settings the app was created with (`create_app(settings)`)."""
    return request.app.state.settings
