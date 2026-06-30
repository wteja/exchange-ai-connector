import keyring
import msal

SERVICE = "exchange-ai-connector"
ACCOUNT = "msal-token-cache"


class AuthError(Exception):
    """Sign-in or token acquisition failed."""


def _load_cache():
    cache = msal.SerializableTokenCache()
    blob = keyring.get_password(SERVICE, ACCOUNT)
    if blob:
        cache.deserialize(blob)
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        keyring.set_password(SERVICE, ACCOUNT, cache.serialize())


def get_token(config, *, force_interactive=False):
    cache = _load_cache()
    app = msal.PublicClientApplication(
        config.client_id, authority=config.authority, token_cache=cache
    )
    scopes = list(config.scopes)
    result = None
    if not force_interactive:
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
    if not result:
        # Authorization Code + PKCE; opens the browser, catches the redirect.
        result = app.acquire_token_interactive(scopes, port=config.redirect_port)
    _save_cache(cache)
    if "access_token" not in result:
        desc = result.get("error_description", "unknown error")
        if "AADSTS65001" in desc:
            raise AuthError(
                "Admin consent required for Mail.Read/Mail.Send on this tenant. "
                "Ask a tenant admin to grant consent, then re-run sign-in. "
                f"Detail: {desc}"
            )
        raise AuthError(f"Sign-in failed: {desc}")
    return result["access_token"]
