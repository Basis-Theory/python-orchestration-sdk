from typing import Dict, Any, Optional
from .config import ProviderConfig, AdyenConfig, CheckoutConfig
from .exceptions import UninitializedError, ConfigurationError
from .providers.adyen import AdyenClient

class PaymentOrchestrationSDK:
    _instance = None

    def __init__(self):
        self.is_test: bool = False
        self.provider_config: Optional[ProviderConfig] = None

    @classmethod
    def init(cls, config: Dict[str, Any]) -> 'PaymentOrchestrationSDK':
        """Initialize the Payment SDK with the provided configuration."""
        if cls._instance is None:
            cls._instance = cls()

        if 'providerConfig' not in config:
            raise ConfigurationError("'providerConfig' parameter is required")

        cls._instance.is_test = config['isTest']

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
                    private_key=checkout_config['privateKey'],
                    public_key=checkout_config['publicKey'],
                    processing_channel=checkout_config.get('processingChannel')
                )
            )

        return cls._instance

    @classmethod
    def get_instance(cls) -> 'PaymentOrchestrationSDK':
        """Get the initialized SDK instance."""
        if cls._instance is None:
            raise UninitializedError("PaymentSDK must be initialized with init() before use")
        return cls._instance

    @property
    def adyen(self) -> AdyenClient:
        """Get the Adyen client instance."""
        if not self.provider_config or not self.provider_config.adyen:
            raise ConfigurationError("Adyen is not configured")

        return AdyenClient(
            api_key=self.provider_config.adyen.api_key,
            merchant_account=self.provider_config.adyen.merchant_account,
            is_test=self.is_test
        )
