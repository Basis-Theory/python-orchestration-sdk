# Getting Started

This guide will help you get started with the Payment Orchestration SDK.

## Prerequisites

- Python 3.7 or higher
- A Basis Theory account and API key
- An account with one of our supported [payment providers](./providers/index.md).

## Installation

Install the SDK using pip:

```bash
pip install payment-orchestration-sdk
```

## Basic Setup

1. First, set up your environment variables:

```bash
# .env file
BASISTHEORY_API_KEY=key_YOUR_BASIS_THEORY_API_KEY
ADYEN_API_KEY=YOUR_ADYEN_API_KEY
ADYEN_MERCHANT_ACCOUNT=YOUR_MERCHANT_ACCOUNT  # If required by your provider
```

2. Initialize the SDK with your chosen provider:

```python
import os
from dotenv import load_dotenv
from orchestration_sdk import PaymentOrchestrationSDK

# Load environment variables
load_dotenv()

# Initialize the SDK with your chosen provider
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,
    'btApiKey': os.environ['BASISTHEORY_API_KEY'],
    'providerConfig': {
        # Configure your chosen provider with their specific configuration
        'adyen': { 
            'apiKey': os.environ['ADYEN_API_KEY'],
            'merchantAccount': os.environ['ADYEN_MERCHANT_ACCOUNT'],
        }
    }
})
```

## Your First Transaction

Here's a complete example of processing a payment:

```python
import os
import uuid
from dotenv import load_dotenv
from orchestration_sdk import PaymentOrchestrationSDK
from orchestration_sdk.models import RecurringType

# Load environment variables
load_dotenv()

async def process_payment():
    # Initialize the SDK with your chosen provider
    sdk = PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': os.environ['BASISTHEORY_API_KEY'],
        'providerConfig': {
            # Configure your chosen provider
            'adyen': {  # Replace with your chosen provider
                'apiKey': os.environ['ADYEN_API_KEY'],
                'merchantAccount': os.environ['ADYEN_MERCHANT_ACCOUNT'],
            }
        }
    })

    # Create a token intent for the card (in a live system this will come from Basis Theory Elements in your frontend)
    import requests
    
    url = "https://api.basistheory.com/token-intents"
    headers = {
        "BT-API-KEY": os.environ['BASISTHEORY_API_KEY'],
        "Content-Type": "application/json"
    }
    payload = {
        "type": "card",
        "data": {
            "number": "4111111145551142",
            "expiration_month": "03",
            "expiration_year": "2030",
            "cvc": "737"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    token_intent_id = response.json()['id']

    # Create a transaction request
    transaction_request = {
        'reference': str(uuid.uuid4()),
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1000,  # $10.00
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token_intent',
            'id': token_intent_id,
            'store_with_provider': False
        },
        'customer': {
            'reference': 'customer-123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
    }

    try:
        # Process the transaction with your chosen provider
        response = await sdk.adyen.transaction(transaction_request)  # Use sdk.<provider>.transaction()
        print(f"Transaction successful: {response}")
        
        return response
        
    except Exception as e:
        print(f"Transaction failed: {e}")
        raise

# Run the payment process
if __name__ == "__main__":
    import asyncio
    asyncio.run(process_payment())
```

## Next Steps

1. Learn about different [payment types](./processing-payments.md)
2. Understand [error handling](./error-handling.md)
3. Set up proper [authentication](./authentication.md)
4. Read your [provider's specific documentation](./providers/index.md)
5. Explore the complete [API reference](./api-reference.md)

## Best Practices

1. **Error Handling**: Always implement proper error handling
2. **API Keys**: Keep your API keys secure and never commit them to version control
3. **Testing**: Use the test environment for development and testing
4. **Logging**: Implement logging for debugging and monitoring
5. **Validation**: Validate all input data before making API calls

## Common Issues

1. **API Key Errors**: Make sure your API keys are correct and have the necessary permissions
2. **Missing Fields**: Check that all required fields are included in your requests
3. **Environment Mismatch**: Ensure you're using the correct environment (test/production)
4. **Invalid Card Data**: Use valid test card numbers in the test environment

## Support

If you encounter any issues:

1. Check the [error handling documentation](./error-handling.md)
2. Review your provider's specific documentation
3. Contact support at [support@example.com](mailto:support@example.com)
4. Open an issue on GitHub 