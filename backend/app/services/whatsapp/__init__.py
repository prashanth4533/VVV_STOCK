"""WhatsApp delivery providers (swappable adapters).

Public API:
    get_provider(name=None) -> WhatsAppProvider
    WhatsAppProvider, SendResult  (from .base)
"""

from app.services.whatsapp.base import WhatsAppProvider, SendResult, WhatsAppError
from app.services.whatsapp.factory import get_provider

__all__ = ["WhatsAppProvider", "SendResult", "WhatsAppError", "get_provider"]
