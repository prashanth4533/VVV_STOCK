"""Resolve a WhatsAppProvider by name.

The active provider is chosen from the `eod.provider` setting (default 'meta').
New providers (e.g. green_api) register here without touching callers.
"""

from app.services.whatsapp.base import WhatsAppProvider, WhatsAppError
from app.services.whatsapp.meta_provider import MetaCloudProvider
from app.services.whatsapp.file_provider import FileProvider


def get_provider(name: str | None = None) -> WhatsAppProvider:
    # Lazy import to avoid a hard dependency on the Setting model at import time.
    if name is None:
        from app.services.settings_service import SettingsService

        name = SettingsService.get("eod.provider", "meta")

    name = (name or "meta").lower()
    if name == "meta":
        return MetaCloudProvider()
    if name == "file":
        return FileProvider()

    raise WhatsAppError(
        f"Unknown WhatsApp provider '{name}'. Supported: meta, file.", retryable=False
    )
