import pytest

from exchange_ai_connector.config import Config, DEFAULT_AUTHORITY
from exchange_ai_connector import config as config_mod


def test_from_env_requires_client_id(monkeypatch):
    monkeypatch.delenv("EXCHANGE_AI_CLIENT_ID", raising=False)
    with pytest.raises(RuntimeError, match="EXCHANGE_AI_CLIENT_ID"):
        Config.from_env()


def test_from_env_defaults(monkeypatch):
    monkeypatch.setenv("EXCHANGE_AI_CLIENT_ID", "abc-123")
    monkeypatch.delenv("EXCHANGE_AI_AUTHORITY", raising=False)
    cfg = Config.from_env()
    assert cfg.client_id == "abc-123"
    assert cfg.authority == DEFAULT_AUTHORITY
    assert cfg.scopes == ("Mail.Read", "Mail.Send", "Calendars.ReadWrite")


def test_from_env_authority_override(monkeypatch):
    monkeypatch.setenv("EXCHANGE_AI_CLIENT_ID", "abc-123")
    monkeypatch.setenv("EXCHANGE_AI_AUTHORITY", "https://login.microsoftonline.com/mytenant")
    assert Config.from_env().authority.endswith("mytenant")


def test_scopes_include_calendar(monkeypatch):
    monkeypatch.setenv("EXCHANGE_AI_CLIENT_ID", "abc-123")
    assert "Calendars.ReadWrite" in Config.from_env().scopes


def test_timezone_env_override(monkeypatch):
    monkeypatch.setenv("EXCHANGE_AI_CLIENT_ID", "abc-123")
    monkeypatch.setenv("EXCHANGE_AI_TIMEZONE", "Asia/Tokyo")
    assert Config.from_env().timezone == "Asia/Tokyo"


def test_timezone_defaults_to_local(monkeypatch):
    monkeypatch.setenv("EXCHANGE_AI_CLIENT_ID", "abc-123")
    monkeypatch.delenv("EXCHANGE_AI_TIMEZONE", raising=False)
    assert Config.from_env().timezone == config_mod._local_tz()


def test_local_tz_falls_back_to_utc(monkeypatch):
    def boom(_):
        raise OSError("no symlink")
    monkeypatch.setattr(config_mod.os, "readlink", boom)
    assert config_mod._local_tz() == "UTC"
