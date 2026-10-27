"""Email communication provider adapters for automated follow-up reminders."""
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Optional
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email

from apps.crm.adapters.base import ProviderDeliveryResult

logger = logging.getLogger("apps.crm.adapters.email")


class BaseEmailAdapter(ABC):
    """Abstract contract for transactional email delivery adapters."""

    def validate_recipient(self, email: str) -> str:
        """Validate and lowercase recipient email address."""
        if not email or not isinstance(email, str):
            raise ValidationError("A valid recipient email address is required.")
        cleaned = email.strip().lower()
        validate_email(cleaned)
        return cleaned

    @abstractmethod
    def send_email(
        self,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        correlation_id: str = "",
    ) -> ProviderDeliveryResult:
        """Deliver an email message to recipient."""
        pass


class SimulatedEmailAdapter(BaseEmailAdapter):
    """Safe local development and test mode email adapter.

    Never attempts external SMTP network connections and marks result as SIMULATED.
    """

    def send_email(
        self,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        correlation_id: str = "",
    ) -> ProviderDeliveryResult:
        try:
            cleaned_recipient = self.validate_recipient(recipient)
        except ValidationError as e:
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message=str(e.message if hasattr(e, "message") else e),
                is_simulated=True,
            )

        simulated_id = f"SIM-EMAIL-{uuid.uuid4().hex[:12].upper()}"
        logger.info(
            f"[SIMULATED_EMAIL] [req:{correlation_id}] Delivered to {cleaned_recipient} | "
            f"Subject: '{subject}' | MessageID: {simulated_id}"
        )
        return ProviderDeliveryResult(
            success=True,
            status="SIMULATED",
            provider_message_id=simulated_id,
            is_simulated=True,
            raw_response={"simulated": True, "recipient": cleaned_recipient, "subject": subject},
        )


class DjangoSMTPEmailAdapter(BaseEmailAdapter):
    """Standard Django SMTP provider adapter using configured email backend."""

    def send_email(
        self,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        correlation_id: str = "",
    ) -> ProviderDeliveryResult:
        try:
            cleaned_recipient = self.validate_recipient(recipient)
        except ValidationError as e:
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message=str(e.message if hasattr(e, "message") else e),
                is_simulated=False,
            )

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@gqt.internal")
        try:
            sent_count = send_mail(
                subject=subject,
                message=body_text,
                from_email=from_email,
                recipient_list=[cleaned_recipient],
                html_message=body_html,
                fail_silently=False,
            )
            msg_id = f"SMTP-{uuid.uuid4().hex[:12].upper()}"
            if sent_count > 0:
                return ProviderDeliveryResult(
                    success=True,
                    status="SENT",
                    provider_message_id=msg_id,
                    is_simulated=False,
                    raw_response={"sent_count": sent_count},
                )
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message="Zero messages sent by SMTP backend.",
                is_simulated=False,
            )
        except Exception as exc:
            logger.error(
                f"[SMTP_EMAIL_FAILURE] [req:{correlation_id}] Failed delivery to {cleaned_recipient}: {exc}"
            )
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message=str(exc),
                is_simulated=False,
            )


def get_email_adapter() -> BaseEmailAdapter:
    """Resolve configured email provider adapter."""
    backend_choice = getattr(settings, "EMAIL_PROVIDER_BACKEND", "simulated").lower()
    if backend_choice == "smtp":
        return DjangoSMTPEmailAdapter()
    return SimulatedEmailAdapter()
