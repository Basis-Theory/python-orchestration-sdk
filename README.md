# Payment Orchestration SDK

The Payment Orchestration SDK is a Python library that simplifies payment processing by providing a unified interface to multiple payment providers. It uses Basis Theory for secure card tokenization and supports multiple payment processors.

## Features

- Unified payment processing interface
- Support for multiple payment providers
- Support for one-time payments and card-on-file transactions
- 3DS authentication support
- Comprehensive error handling and categorization
- [Providers](./docs/providers/index.md) documentation for each provider supported by the SDK.

## Installation

```bash
pip install payment-orchestration-sdk
```

## Quick Start

```python
from payment_orchestration_sdk import PaymentOrchestrationSDK
from payment_orchestration_sdk.models import RecurringType

# Initialize the SDK with your chosen provider
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,  # Use test environment
    'btApiKey': 'YOUR_BASIS_THEORY_API_KEY',
    'providerConfig': {
        # Configure your chosen provider
        'adyen': {
            'apiKey': 'YOUR_PROVIDER_API_KEY',
            'merchantAccount': 'YOUR_MERCHANT_ACCOUNT',
        }
    }
})

# Create a transaction request
transaction_request = {
    'reference': 'unique-transaction-reference',
    'type': RecurringType.ONE_TIME,
    'amount': {
        'value': 1000,  # Amount in cents
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': 'YOUR_BASIS_THEORY_TOKEN_ID',
        'store_with_provider': False
    },
    'customer': {
        'reference': 'customer-reference',
    }
}

# Process the transaction with your chosen provider
response = await sdk.adyen.transaction(transaction_request)  # Use sdk.<provider>.transaction()
```

## Documentation

- [Getting Started](./docs/getting-started.md)
- [Authentication](./docs/authentication.md)
- [Processing Payments](./docs/processing-payments.md)
- [Error Handling](./docs/error-handling.md)
- [API Reference](./docs/api-reference.md)
- [Providers](./docs/providers/index.md)

## Support

For support, please contact [support@basistheory.com](mailto:support@basistheory.com) or open an issue on GitHub. 