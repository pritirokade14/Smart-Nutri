import pytest

from app.core.config import Settings, get_settings


def test_allowed_origins_from_comma_string(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,https://smartnutri.in")
    assert Settings(_env_file=None).allowed_origins == [
        "http://localhost:3000",
        "https://smartnutri.in",
    ]


def test_settings_ignore_dotenv_in_cwd(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("SUPABASE_URL=https://leaked.example\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    assert Settings(_env_file=None).supabase_url == ""
    # the autouse fixture also disables the default env_file
    assert Settings().supabase_url == ""
    assert get_settings().supabase_url == ""


def test_voice_transcode_mimes_from_comma_string(monkeypatch):
    monkeypatch.setenv("VOICE_TRANSCODE_MIMES", "audio/webm, Audio/Ogg,,")
    assert Settings(_env_file=None).voice_transcode_mimes == frozenset({"audio/webm", "audio/ogg"})


def test_voice_transcode_mimes_default_transcodes_every_non_wav():
    assert Settings(_env_file=None).voice_transcode_mimes == frozenset(
        {"audio/mp4", "audio/webm", "audio/ogg", "audio/mpeg"}
    )


def test_wildcard_origin_rejected():
    with pytest.raises(ValueError):
        Settings(_env_file=None, allowed_origins=["*"])


def test_wildcard_origin_rejected_from_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://a.example,*")
    with pytest.raises(ValueError):
        Settings(_env_file=None)
