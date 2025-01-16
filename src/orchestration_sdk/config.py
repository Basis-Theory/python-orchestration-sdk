from dataclasses import dataclass
from typing import Optional

@dataclass
class AdyenConfig:
    api_key: str
    merchant_account: str
    production_prefix: Optional[str] = ""

@dataclass
class CheckoutConfig:
    private_key: str
    processing_channel: Optional[str] = None

@dataclass
class ProviderConfig:
    adyen: Optional[AdyenConfig] = None
    checkout: Optional[CheckoutConfig] = None
