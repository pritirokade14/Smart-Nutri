from functools import cache
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Request
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.core.i18n import repo_messages_dir

# `reasoning_effort` values CallMissed accepts on chat completions (docs: chat-completion).
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
SPEECH_LANGUAGES = ("en", "hi", "mr")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["dev", "staging", "prod", "test"] = "dev"
    # Root log level (env LOG_LEVEL). Independent of `environment`: DEBUG can log SQL/HTTP detail.
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    callmissed_api_key: SecretStr | None = None
    callmissed_base_url: str = "https://api.callmissed.com/v1"
    callmissed_resource_url: str = "https://api.callmissed.com/api/v1"
    # Model ids per AI job (ADR 0021, docs/SETUP_ACCOUNTS.md "CallMissed AI setup"). Every
    # default is processed in India (catalogue `processing: "india"`, read 2026-11-04) and is
    # in app.integrations.callmissed.INDIA_PROCESSED_MODELS. A fallback model is tried once,
    # inside the same deadline, when the primary answers 5xx, times out, or is refused with
    # `region_unavailable`. An empty env value turns a fallback off.
    #
    # Label extraction (vision, strict JSON). The label eval compares gpt-4o, gemma-4-31b,
    # glm-5.3-flash and deepseek-v4.1-flash-1017 before the final choice.
    callmissed_extraction_model: str = "gpt-4o"
    callmissed_extraction_fallback_model: str | None = "glm-5.3-flash"
    callmissed_extraction_reasoning_effort: ReasoningEffort | None = "none"
    # Label-extraction prompt (env EXTRACTION_PROMPT_VERSION). v2 returns raw cell text parsed
    # in code (app/features/scans/cells.py); v1 stays selectable so the eval can compare them.
    # Part of the extraction cache key, so switching never reuses the other version's output.
    extraction_prompt_version: Literal["extraction_v1", "extraction_v2"] = "extraction_v1"
    # Explanations and voice answers (text, strict JSON, 8 s budget). sarvam-105b stays
    # selectable but is not the default: it timed out at 8 s.
    callmissed_explanation_model: str = "gpt-4o"
    callmissed_explanation_fallback_model: str | None = "gemma-4-31b"
    # Sent as `reasoning_effort` (docs: api-speed). "none" switches thinking off where the
    # model allows it (gemma-4-31b, sarvam-105b); gpt-4o ignores it; glm-5.3-flash runs "low".
    callmissed_explanation_reasoning_effort: ReasoningEffort | None = "none"
    # Speech-to-text (POST /v1/audio/transcriptions). `*_languages` maps en/hi/mr to the
    # `language` form field; a language missing from the map is left out (auto-detect).
    callmissed_stt_model: str = "saaras:v4"
    callmissed_stt_fallback_model: str | None = "whisper"
    callmissed_stt_languages: dict[str, str] = {"en": "en-IN", "hi": "hi-IN", "mr": "mr-IN"}
    # Whisper's language codes are not documented by CallMissed: let it auto-detect.
    callmissed_stt_fallback_languages: dict[str, str] = {}
    # Text-to-speech (POST /v1/audio/speech, mp3). Voices per language, from the CallMissed
    # voices page: bulbul:v3 recommends ratan for en-IN and mr-IN, shubh for hi-IN. Gnani
    # Timbre v3 voices speak every Indian language; Chetana is its healthcare voice.
    # microsoft-neural-tts is processed in India but serves voice sessions only (400 here).
    callmissed_tts_model: str = "bulbul:v3"
    callmissed_tts_voices: dict[str, str] = {"en": "ratan", "hi": "shubh", "mr": "ratan"}
    callmissed_tts_fallback_model: str | None = "gnani-timbre-v3.0"
    callmissed_tts_fallback_voices: dict[str, str] = {
        "en": "Chetana",
        "hi": "Chetana",
        "mr": "Chetana",
    }
    # packages/i18n/messages (spoken fallback answers). /app/i18n in the Docker image.
    i18n_messages_dir: Path = Field(default_factory=repo_messages_dir)
    supabase_url: str = ""
    supabase_project_ref: str = ""
    supabase_jwks_url: str = ""
    supabase_secret_key: SecretStr | None = None
    supabase_storage_bucket: str = "label-photos"
    # POST /v1/voice/ask answers 503 `ai_unavailable` while false (Ruling V1 S3). Stays false
    # on dev and prod until the user approves the paid end-to-end CallMissed probe
    # (scripts/probe_callmissed.py --yes-spend). No voice audio is stored (ADR 0020).
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
    # Process-wide cap on Open Food Facts search calls (text and category), a token bucket
    # (I4). OFF allows about 10 search requests a minute per client; cache hits are free.
    off_search_per_minute: int = Field(default=8, ge=1)
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
    # Ruling D1/S5: POST /v1/consents and DELETE /v1/me (each account, per UTC day).
    rate_limit_consents_per_day: int = 60
    rate_limit_account_deletes_per_day: int = 5
    # m6: POST /v1/members and PATCH /v1/members/{id} together (each account, per UTC day).
    rate_limit_member_writes_per_day: int = 60
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

    @field_validator(
        "callmissed_extraction_fallback_model",
        "callmissed_explanation_fallback_model",
        "callmissed_stt_fallback_model",
        "callmissed_tts_fallback_model",
        "callmissed_extraction_reasoning_effort",
        "callmissed_explanation_reasoning_effort",
        mode="before",
    )
    @classmethod
    def _empty_is_none(cls, v: Any) -> Any:
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("callmissed_stt_languages", "callmissed_tts_voices")
    @classmethod
    def _every_language(cls, v: dict[str, str]) -> dict[str, str]:
        missing = [lang for lang in SPEECH_LANGUAGES if not v.get(lang)]
        if missing:
            raise ValueError(f"needs a value for every language; missing {missing}")
        return v

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
