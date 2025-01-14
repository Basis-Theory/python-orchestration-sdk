from typing import Optional, Dict, Any
from dataclasses import dataclass
from .providers.adyen import AdyenClient
from .providers.checkout import CheckoutClient
from .exceptions import ConfigurationError


@dataclass
class AdyenConfig:
    api_key: str
    merchant_account: str


@dataclass
class CheckoutConfig:
    private_key: str
    processing_channel: str


@dataclass
class ProviderConfig:
    adyen: Optional[AdyenConfig] = None
    checkout: Optional[CheckoutConfig] = None


class PaymentOrchestrationSDK:
    _instance = None

    def __init__(self):
        self.is_test: bool = False
        self.bt_api_key: Optional[str] = None
        self.provider_config: Optional[ProviderConfig] = None

    @classmethod
    def init(cls, config: Dict[str, Any]) -> 'PaymentOrchestrationSDK':
        """Initialize the Payment Orchestration SDK with the provided configuration."""
        if cls._instance is None:
            cls._instance = cls()

        if 'isTest' not in config:
            raise ConfigurationError("'isTest' parameter is required")
        if 'btApiKey' not in config:
            raise ConfigurationError("'btApiKey' parameter is required")
        if 'providerConfig' not in config:
            raise ConfigurationError("'providerConfig' parameter is required")

        cls._instance.is_test = config['isTest']
        cls._instance.bt_api_key = config['btApiKey']

        provider_config = config['providerConfig']

        # Initialize Adyen configuration if provided
        if 'adyen' in provider_config:
            adyen_config = provider_config['adyen']
            cls._instance.provider_config = ProviderConfig(
                adyen=AdyenConfig(
                    api_key=adyen_config['apiKey'],
                    merchant_account=adyen_config['merchantAccount']
                )
            )

        # Initialize Checkout.com configuration if provided
        if 'checkout' in provider_config:
            checkout_config = provider_config['checkout']
            cls._instance.provider_config = ProviderConfig(
                checkout=CheckoutConfig(
                    private_key=checkout_config['private_key'],
                    processing_channel=checkout_config.get('processing_channel')
                )
            )

        return cls._instance

    @classmethod
    def get_instance(cls) -> 'PaymentOrchestrationSDK':
        """Get the initialized SDK instance."""
        if cls._instance is None:
            raise ConfigurationError("PaymentOrchestrationSDK must be initialized with init() before use")
        return cls._instance

    @property
    def adyen(self) -> AdyenClient:
        """Get the Adyen client instance."""
        if not self.provider_config or not self.provider_config.adyen:
            raise ConfigurationError("Adyen is not configured")

        return AdyenClient(
            api_key=self.provider_config.adyen.api_key,
            merchant_account=self.provider_config.adyen.merchant_account,
            is_test=self.is_test,
            bt_api_key=self.bt_api_key
        )

    @property
    def checkout(self) -> CheckoutClient:
        """Get the Checkout client instance."""
        if not self.provider_config or not self.provider_config.checkout:
            raise ConfigurationError("Checkout is not configured")

        return CheckoutClient(
            private_key=self.provider_config.checkout.private_key,
            processing_channel=self.provider_config.checkout.processing_channel,
            is_test=self.is_test,
            bt_api_key=self.bt_api_key
        )