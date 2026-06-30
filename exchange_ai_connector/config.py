import os
from dataclasses import dataclass, field

DEFAULT_AUTHORITY = "https://login.microsoftonline.com/common"
DEFAULT_SCOPES = ("Mail.Read", "Mail.Send", "Calendars.ReadWrite")


def _local_tz() -> str:
    # ponytail: read /etc/localtime symlink (macOS/Linux) for the IANA name;
    # EXCHANGE_AI_TIMEZONE overrides. Falls back to UTC if the symlink is absent.
    try:
        return os.readlink("/etc/localtime").split("zoneinfo/")[-1]
    except OSError:
        return "UTC"


@dataclass(frozen=True)
class Config:
    client_id: str
    authority: str = DEFAULT_AUTHORITY
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    redirect_port: int = 8400
    timezone: str = field(default_factory=_local_tz)

    @classmethod
    def from_env(cls) -> "Config":
        client_id = os.environ.get("EXCHANGE_AI_CLIENT_ID")
        if not client_id:
            raise RuntimeError(
                "EXCHANGE_AI_CLIENT_ID is not set. Register an app in Entra ID "
                "(multi-tenant + personal accounts) and export its Application "
                "(client) ID as EXCHANGE_AI_CLIENT_ID."
            )
        return cls(
            client_id=client_id,
            authority=os.environ.get("EXCHANGE_AI_AUTHORITY", DEFAULT_AUTHORITY),
            timezone=os.environ.get("EXCHANGE_AI_TIMEZONE") or _local_tz(),
        )
