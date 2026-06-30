from unittest.mock import MagicMock, patch

import pytest

from exchange_ai_connector import auth
from exchange_ai_connector.config import Config

CFG = Config(client_id="cid", redirect_port=8400)


@pytest.fixture
def fake_keyring(monkeypatch):
    store = {}
    monkeypatch.setattr(auth.keyring, "get_password",
                        lambda s, a: store.get((s, a)))
    monkeypatch.setattr(auth.keyring, "set_password",
                        lambda s, a, v: store.__setitem__((s, a), v))
    return store


def _fake_app(silent=None, interactive=None):
    app = MagicMock()
    app.get_accounts.return_value = [{"username": "me"}] if silent else []
    app.acquire_token_silent.return_value = silent
    app.acquire_token_interactive.return_value = interactive
    return app


def test_silent_token_when_account_exists(fake_keyring):
    app = _fake_app(silent={"access_token": "SILENT"})
    with patch.object(auth.msal, "PublicClientApplication", return_value=app):
        token = auth.get_token(CFG)
    assert token == "SILENT"
    app.acquire_token_interactive.assert_not_called()


def test_interactive_when_no_account(fake_keyring):
    app = _fake_app(silent=None, interactive={"access_token": "INTERACTIVE"})
    with patch.object(auth.msal, "PublicClientApplication", return_value=app):
        token = auth.get_token(CFG)
    assert token == "INTERACTIVE"
    app.acquire_token_interactive.assert_called_once()


def test_force_interactive_skips_silent(fake_keyring):
    app = _fake_app(silent={"access_token": "SILENT"},
                    interactive={"access_token": "FORCED"})
    with patch.object(auth.msal, "PublicClientApplication", return_value=app):
        token = auth.get_token(CFG, force_interactive=True)
    assert token == "FORCED"
    app.acquire_token_silent.assert_not_called()
    app.get_accounts.assert_not_called()


def test_admin_consent_error_is_friendly(fake_keyring):
    app = _fake_app(interactive={"error": "consent_required",
                                 "error_description": "AADSTS65001: needs admin"})
    with patch.object(auth.msal, "PublicClientApplication", return_value=app):
        with pytest.raises(auth.AuthError, match="Admin consent"):
            auth.get_token(CFG)


def test_cache_saved_to_keyring(fake_keyring):
    app = _fake_app(silent=None, interactive={"access_token": "T"})

    def build(*a, **k):
        k["token_cache"].has_state_changed = True
        k["token_cache"].serialize = lambda: "CACHE_BLOB"
        return app

    with patch.object(auth.msal, "PublicClientApplication", side_effect=build):
        auth.get_token(CFG)
    assert fake_keyring[(auth.SERVICE, auth.ACCOUNT)] == "CACHE_BLOB"


def test_cache_not_saved_when_unchanged(fake_keyring):
    app = _fake_app(silent=None, interactive={"access_token": "T"})

    def build(*a, **k):
        k["token_cache"].has_state_changed = False
        k["token_cache"].serialize = lambda: "CACHE_BLOB"
        return app

    with patch.object(auth.msal, "PublicClientApplication", side_effect=build):
        auth.get_token(CFG)
    assert (auth.SERVICE, auth.ACCOUNT) not in fake_keyring
