from app.core.config import Settings


def test_allowed_origins_from_comma_string(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,https://smartnutri.in")
    assert Settings(_env_file=None).allowed_origins == [
        "http://localhost:3000",
        "https://smartnutri.in",
    ]
