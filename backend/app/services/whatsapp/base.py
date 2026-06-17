"""Provider-agnostic WhatsApp interface.

A provider knows how to deliver a message to a single recipient and report
back a normalised result. The cron job / delivery service handles retries,
DB logging and status rollup — providers stay thin and stateless.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class WhatsAppError(Exception):
    """Raised on a delivery failure.

    `retryable` tells the caller whether a retry could plausibly succeed
    (network blip, 5xx, rate limit) vs a permanent error (bad number,
    unapproved template, auth failure).
    """

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


@dataclass
class SendResult:
    success: bool
    provider_msg_id: str | None = None
    error: str | None = None


class WhatsAppProvider(ABC):
    name: str = "base"

    @abstractmethod
    def send_text(self, to: str, message: str) -> SendResult:
        """Send a free-form text message.

        For Meta this only succeeds inside the 24h customer-service window;
        for scheduled/unsolicited pushes use send_template(). Always works for
        the Admin "Test Send" button (assuming a recent inbound) and for
        providers that have no template concept (e.g. Green API)."""
        ...

    def send_template(
        self, to: str, template_name: str, lang: str, params: list[str]
    ) -> SendResult:
        """Send a pre-approved template message. Default: not supported.

        Providers that support templates (Meta) override this. Providers that
        don't (Green API) leave the default, and callers fall back to
        send_text()."""
        raise WhatsAppError(
            f"{self.name} does not support template messages.", retryable=False
        )
