"""Provider adapters package for CRM communications."""
from apps.crm.adapters.base import ProviderDeliveryResult
from apps.crm.adapters.email import BaseEmailAdapter, SimulatedEmailAdapter, get_email_adapter
from apps.crm.adapters.whatsapp import BaseWhatsAppAdapter, SimulatedWhatsAppAdapter, get_whatsapp_adapter

__all__ = [
    "ProviderDeliveryResult",
    "BaseEmailAdapter",
    "SimulatedEmailAdapter",
    "get_email_adapter",
    "BaseWhatsAppAdapter",
    "SimulatedWhatsAppAdapter",
    "get_whatsapp_adapter",
]
