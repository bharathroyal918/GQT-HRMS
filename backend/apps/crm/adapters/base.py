"""Base interfaces and data structures for CRM communication provider adapters."""
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ProviderDeliveryResult:
    """Unified result structure returned by external communication provider adapters."""

    success: bool
    status: str = "FAILED"  # SENT, DELIVERED, FAILED, SIMULATED
    provider_message_id: str = ""
    error_message: str = ""
    is_simulated: bool = False
    is_transient: bool = False
    raw_response: Dict[str, Any] = field(default_factory=dict)
