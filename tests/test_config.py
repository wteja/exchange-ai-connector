import pytest

from exchange_ai_connector.config import Config, DEFAULT_AUTHORITY


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
    assert cfg.scopes == ("Mail.Read", "Mail.Send")


def test_from_env_authority_override(monkeypatch):
    monkeypatch.setenv("EXCHANGE_AI_CLIENT_ID", "abc-123")
    monkeypatch.setenv("EXCHANGE_AI_AUTHORITY", "https://login.microsoftonline.com/mytenant")
    assert Config.from_env().authority.endswith("mytenant")
