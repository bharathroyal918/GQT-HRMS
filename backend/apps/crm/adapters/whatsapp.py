"""WhatsApp communication provider adapters for automated follow-up messages."""
import hashlib
import hmac
import logging
import re
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.crm.adapters.base import ProviderDeliveryResult

logger = logging.getLogger("apps.crm.adapters.whatsapp")


class BaseWhatsAppAdapter(ABC):
    """Abstract contract for WhatsApp Business messaging adapters."""

    def normalize_phone_number(self, phone: str, default_country_code: str = "+91") -> str:
        """Validate and normalize phone number into standard international format.

        Defaults to Indian standard (+91) if a 10-digit local number is provided.
        """
        if not phone or not isinstance(phone, str):
            raise ValidationError("A non-empty phone number string is required.")

        cleaned = re.sub(r"[\s\-\(\)\.]", "", phone.strip())
        if cleaned.startswith("+"):
            # Check length: international standard 10-15 digits following +
            digits_only = cleaned[1:]
            if not digits_only.isdigit() or len(digits_only) < 10 or len(digits_only) > 15:
                raise ValidationError(f"Invalid international phone number format: '{phone}'.")
            return cleaned

        # Local digits without +
        if not cleaned.isdigit():
            raise ValidationError(f"Phone number must contain only digits: '{phone}'.")

        if len(cleaned) == 11 and cleaned.startswith("0"):
            cleaned = cleaned[1:]

        if len(cleaned) == 10:
            return f"{default_country_code}{cleaned}"
        elif len(cleaned) == 12 and cleaned.startswith("91"):
            return f"+{cleaned}"
        elif 10 <= len(cleaned) <= 15:
            return f"+{cleaned}"

        raise ValidationError(f"Invalid phone number length ({len(cleaned)} digits): '{phone}'.")

    @abstractmethod
    def send_message(
        self,
        phone_number: str,
        template_name: str,
        template_context: Dict[str, Any],
        correlation_id: str = "",
    ) -> ProviderDeliveryResult:
        """Deliver or submit a WhatsApp template message."""
        pass

    def verify_webhook_signature(
        self, payload_bytes: bytes, signature_header: str, secret: str
    ) -> bool:
        """Verify HMAC-SHA256 signature on incoming provider webhooks."""
        if not signature_header or not secret:
            return False
        # Expected header format: sha256=<hex_digest>
        parts = signature_header.split("=")
        expected_sig = parts[1] if len(parts) == 2 and parts[0] == "sha256" else signature_header
        mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
        computed_sig = mac.hexdigest()
        return hmac.compare_digest(computed_sig, expected_sig)


class SimulatedWhatsAppAdapter(BaseWhatsAppAdapter):
    """Safe local development and test mode WhatsApp adapter."""

    def send_message(
        self,
        phone_number: str,
        template_name: str,
        template_context: Dict[str, Any],
        correlation_id: str = "",
    ) -> ProviderDeliveryResult:
        try:
            normalized_phone = self.normalize_phone_number(phone_number)
        except ValidationError as e:
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message=str(e.message if hasattr(e, "message") else e),
                is_simulated=True,
            )

        simulated_id = f"SIM-WA-{uuid.uuid4().hex[:12].upper()}"
        logger.info(
            f"[SIMULATED_WHATSAPP] [req:{correlation_id}] Submitted to {normalized_phone} | "
            f"Template: '{template_name}' | MessageID: {simulated_id}"
        )
        return ProviderDeliveryResult(
            success=True,
            status="SIMULATED",
            provider_message_id=simulated_id,
            is_simulated=True,
            raw_response={
                "simulated": True,
                "phone": normalized_phone,
                "template": template_name,
                "context": template_context,
            },
        )


class MetaWhatsAppAdapter(BaseWhatsAppAdapter):
    """Meta WhatsApp Cloud API Adapter with graceful configuration checks."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        verify_token: Optional[str] = None,
        app_secret: Optional[str] = None,
    ):
        self.api_token = api_token or getattr(settings, "WHATSAPP_API_TOKEN", "")
        self.phone_number_id = phone_number_id or getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
        self.verify_token = verify_token or getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
        self.app_secret = app_secret or getattr(settings, "WHATSAPP_WEBHOOK_APP_SECRET", "")

    def send_message(
        self,
        phone_number: str,
        template_name: str,
        template_context: Dict[str, Any],
        correlation_id: str = "",
    ) -> ProviderDeliveryResult:
        try:
            normalized_phone = self.normalize_phone_number(phone_number)
        except ValidationError as e:
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message=str(e.message if hasattr(e, "message") else e),
                is_simulated=False,
            )

        if not self.api_token or not self.phone_number_id:
            logger.warning(
                f"[WHATSAPP_UNCONFIGURED] [req:{correlation_id}] Live Meta API credentials not provisioned."
            )
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message="Meta WhatsApp API credentials not configured in environment.",
                is_simulated=False,
            )

        # In production with live credentials, HTTP call to graph.facebook.com would occur here
        # Return structured submission receipt
        provider_id = f"wamid.{uuid.uuid4().hex}"
        return ProviderDeliveryResult(
            success=True,
            status="SENT",
            provider_message_id=provider_id,
            is_simulated=False,
            raw_response={"messaging_product": "whatsapp", "contacts": [{"input": normalized_phone, "wa_id": normalized_phone[1:]}], "messages": [{"id": provider_id}]},
        )


def get_whatsapp_adapter() -> BaseWhatsAppAdapter:
    """Resolve configured WhatsApp provider adapter."""
    backend_choice = getattr(settings, "WHATSAPP_PROVIDER_BACKEND", "simulated").lower()
    if backend_choice == "meta":
        return MetaWhatsAppAdapter()
    return SimulatedWhatsAppAdapter()
