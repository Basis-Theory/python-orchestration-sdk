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

You can create an API key with these permissions in the [Basis Theory Portal](https://portal.basistheory.com).