# Authentication

This guide explains how to set up authentication for both Basis Theory and Adyen in the Payment Orchestration SDK.

## Required API Keys

You'll need the following API keys:

1. **Basis Theory API Key**: Used for tokenizing card data
2. Any [Provider](./providers/index.md) API Key: Used for processing payments

## Environment Setup

We recommend using environment variables to manage your API keys:

```bash
# .env file
BASISTHEORY_API_KEY=key_YOUR_BASIS_THEORY_API_KEY
ADYEN_API_KEY=YOUR_ADYEN_API_KEY
ADYEN_MERCHANT_ACCOUNT=YOUR_MERCHANT_ACCOUNT
```

Then in your code:

```python
import os
from dotenv import load_dotenv
from payment_orchestration_sdk import PaymentOrchestrationSDK

# Load environment variables
load_dotenv()

# Initialize the SDK
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,  # Set to False for production
    'btApiKey': os.environ['BASISTHEORY_API_KEY'],
    'providerConfig': {
        'adyen': {
            'apiKey': os.environ['ADYEN_API_KEY'],
            'merchantAccount': os.environ['ADYEN_MERCHANT_ACCOUNT'],
        }
    }
})
```

## Basis Theory API Key Requirements

Your Basis Theory API key needs the following permissions:

- `token:use`
- `token_intent:use`

You can create an API key with these permissions in the [Basis Theory Portal](https://portal.basistheory.com).

## Test Environment

To utilize the providers test environment, set the `isTest` flag to `True` in the SDK initialization.

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,  # Enable test environment
    ...
})
```

## API Key Security

Best practices for API key security:

1. Never commit API keys to version control
2. Use environment variables or a secure secrets manager
3. Rotate API keys periodically
4. Use different API keys for test and production environments
5. Follow the principle of least privilege when assigning permissions

## Error Handling

If your API keys are invalid or expired, you'll receive an authentication error:

```python
try:
    response = await sdk.adyen.transaction(transaction_request)
except Exception as e:
    # Handle authentication errors
    if e.error_codes[0]['category'] == ErrorCategory.AUTHENTICATION_ERROR:
        if e.error_codes[0]['code'] == 'invalid_api_key':
            print("Invalid API key")
        elif e.error_codes[0]['code'] == 'unauthorized':
            print("Unauthorized request")
```

## Troubleshooting

Common authentication issues:

1. **Invalid API Key**: Verify the API key is correct and has the required permissions
2. **Wrong Environment**: Ensure you're using test keys for test environment and production keys for production
3. **Missing Permissions**: Check that your Basis Theory API key has all required permissions
4. **Expired Key**: Verify your API keys haven't expired
5. **Invalid Merchant Account**: Confirm your Adyen merchant account is correct and matches the environment 