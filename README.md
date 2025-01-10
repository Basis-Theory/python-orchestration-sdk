# Payment Orchestration SDK

The Payment Orchestration SDK is a Python library that simplifies payment processing by providing a unified interface to multiple payment providers. It uses Basis Theory for secure card tokenization and supports multiple payment processors.

## Features

- Unified payment processing interface
- Secure card tokenization with Basis Theory
- Support for multiple payment providers
- Support for one-time payments and card-on-file transactions
- 3DS authentication support
- Comprehensive error handling and categorization
- Type hints and dataclass models for better IDE support
- [Providers](./providers/index.md) documentation for each provider supported by the SDK.

## Documentation

- [Getting Started](./getting-started.md)
- [Authentication](./authentication.md)
- [Processing Payments](./processing-payments.md)
- [Error Handling](./error-handling.md)
- [API Reference](./api-reference.md)
- [Providers](./providers/index.md)

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

## Support

For support, please contact [support@basistheory.com](mailto:support@basistheory.com) or open an issue on GitHub. 

## Development

To contribute to the SDK:

1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install development dependencies: `pip install -e ".[test]"`
5. Make your changes
6. Run tests to ensure everything works
7. Submit a pull request

### Running Tests

1. Set up your environment variables:
```bash
export BASISTHEORY_API_KEY='your_basis_theory_api_key'
export ADYEN_API_KEY='your_adyen_api_key'
export ADYEN_MERCHANT_ACCOUNT='your_merchant_account'
```

2. Run the tests:
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src/

# Run a specific test file
python test.py
```

## License

[Add your license information here] 