# Checkout.com Provider

This guide explains how to use Checkout.com as a payment provider with the Payment Orchestration SDK.

## Configuration

Configure Checkout.com in the SDK initialization:

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,  # Set to False for production
    'btApiKey': os.environ['BASISTHEORY_API_KEY'],
    'providerConfig': {
        'checkout': {
            'private_key': os.environ['CHECKOUT_PRIVATE_KEY'],
            'processing_channel': os.environ['CHECKOUT_PROCESSING_CHANNEL']  # Optional
        }
    }
})
```

## Required Credentials

1. **Checkout.com Private Key**: Your Checkout.com secret key for authentication
2. **Processing Channel ID**: (Optional) Your Checkout.com processing channel identifier

You can obtain these credentials from your [Checkout.com Dashboard](https://dashboard.checkout.com/).

## Test Cards

For testing, use these Checkout.com test card numbers:

- **Visa**: 4242424242424242
- **Mastercard**: 5555555555554444
- **American Express**: 378282246310005

## Processing Payments

### One-Time Payment

```python
response = await sdk.checkout.transaction({
    'reference': str(uuid.uuid4()),
    'type': RecurringType.ONE_TIME,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': token_id,
        'store_with_provider': False
    }
})
```

### Card-on-File Payment

```python
response = await sdk.checkout.transaction({
    'reference': str(uuid.uuid4()),
    'type': RecurringType.UNSCHEDULED,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': token_id,
        'store_with_provider': True,
        'holderName': 'John Doe'
    },
    'customer': {
        'reference': str(uuid.uuid4()),
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
})

# Store the processor token for future use
processor_token = response['source']['provisioned']['id']
```

### 3DS Payment

```python
response = await sdk.checkout.transaction({
    'reference': str(uuid.uuid4()),
    'type': RecurringType.ONE_TIME,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': token_id
    },
    'three_ds': {
        'eci': '05',
        'authentication_value': 'YOUR_3DS_AUTH_VALUE',
        'xid': 'YOUR_3DS_XID',
        'version': '2.2.0'
    }
})
```

### Using Stored Cards

```python
response = await sdk.checkout.transaction({
    'reference': str(uuid.uuid4()),
    'type': RecurringType.UNSCHEDULED,
    'merchant_initiated': True,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'processor_token',
        'id': 'PREVIOUSLY_STORED_PROCESSOR_TOKEN'
    }
})
```


## Environment Support

### Test Environment

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,
    'providerConfig': {
        'checkout': {
            'private_key': 'YOUR_TEST_CHECKOUT_PRIVATE_KEY',
            'processing_channel': 'YOUR_TEST_PROCESSING_CHANNEL'
        }
    }
})
```

### Production Environment

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': False,
    'providerConfig': {
        'checkout': {
            'private_key': 'YOUR_PRODUCTION_CHECKOUT_PRIVATE_KEY',
            'processing_channel': 'YOUR_PRODUCTION_PROCESSING_CHANNEL'
        }
    }
})
``` 