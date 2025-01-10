# Payment Orchestration SDK

A Python SDK for seamless payment processing, built on top of Basis Theory's secure tokenization platform.

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/your-org/payment-orchestration-sdk.git

# For development, clone the repository and install with test dependencies
git clone https://github.com/your-org/payment-orchestration-sdk.git
cd payment-orchestration-sdk
pip install -e ".[test]"
```

## Requirements

- Python 3.7 or higher
- A Basis Theory API key
- Payment provider credentials (e.g., Adyen API key and merchant account)

## Usage

Here's a basic example of how to use the SDK:

```python
from payment_orchestration_sdk import PaymentOrchestrationSDK

# Initialize the SDK
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,
    'btApiKey': 'your_basis_theory_api_key',
    'providerConfig': {
        'adyen': {
            'apiKey': 'your_adyen_api_key',
            'merchantAccount': 'your_merchant_account',
        }
    }
})

# Create a transaction request
transaction_request = {
    'amount': {
        'value': 1000,  # Amount in cents
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': 'your_token_id',
        'store_with_provider': False
    },
    'customer': {
        'reference': 'customer_123',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'address': {
            'address_line1': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001',
            'country': 'US'
        }
    }
}

# Process the transaction
response = await sdk.adyen.transaction(transaction_request)
```

## Running Tests

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

## Configuration

The SDK supports the following configuration options when initializing:

- `isTest`: Boolean flag to indicate if using test environment
- `btApiKey`: Your Basis Theory API key
- `providerConfig`: Configuration for payment providers
  - `adyen`: Adyen-specific configuration
    - `apiKey`: Adyen API key
    - `merchantAccount`: Adyen merchant account

## Error Handling

The SDK uses standard Python exceptions for error handling. Always wrap your SDK calls in try-except blocks:

```python
try:
    response = await sdk.adyen.transaction(transaction_request)
except Exception as e:
    print(f"Error occurred: {str(e)}")
```

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

## License

[Add your license information here] 