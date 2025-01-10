# Adyen Provider

This guide explains how to use Adyen as a payment provider with the Payment Orchestration SDK.

## Configuration

Configure Adyen in the SDK initialization:

```python
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

## Required Credentials

1. **Adyen API Key**: Your Adyen API key for authentication
2. **Merchant Account**: Your Adyen merchant account identifier

You can obtain these credentials from your [Adyen Customer Area](https://ca-test.adyen.com/ca/ca/overview/default.shtml).

## Test Cards

For testing, use these Adyen test card numbers:

- **Regular Card**: 4111111145551142
- **3DS Card**: 4917610000000000
- **Expired Card**: Use any valid card number with `holderName: "CARD_EXPIRED"`

## Processing Payments

### One-Time Payment

```python
response = await sdk.adyen.transaction({
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
response = await sdk.adyen.transaction({
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
    }
})

# Store the processor token for future use
processor_token = response['source']['provisioned']['id']
```

### 3DS Payment

```python
response = await sdk.adyen.transaction({
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
response = await sdk.adyen.transaction({
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

## Provider-Specific Error Codes

Adyen-specific error codes are mapped to standardized error categories:

| Adyen Code | Description | SDK Error Category |
|------------|-------------|-------------------|
| 6 | Expired Card | PAYMENT_METHOD_ERROR |
| 05 | Insufficient Funds | PAYMENT_METHOD_ERROR |
| 14 | Invalid Card | PAYMENT_METHOD_ERROR |
| 2 | Refused | PROCESSING_ERROR |
| 3 | Referral | PROCESSING_ERROR |
| 8 | Authentication Failed | PAYMENT_METHOD_ERROR |
| 101 | Invalid API Key | AUTHENTICATION_ERROR |

## Response Format

Adyen responses are standardized to match the SDK's response format:

```python
{
    'id': 'transaction-id',
    'reference': 'your-reference',
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'status': {
        'code': TransactionStatusCode.AUTHORIZED,
        'provider_code': 'Authorised'  # Original Adyen status
    },
    'source': {
        'type': 'basis_theory_token',
        'id': 'token-id',
        'provisioned': {
            'id': 'processor-token'  # Adyen recurring token
        }
    },
    'networkTransactionId': 'network-transaction-id',
    'full_provider_response': {
        # Raw Adyen response
    }
}
```

## Environment Support

### Test Environment

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,
    'providerConfig': {
        'adyen': {
            'apiKey': 'YOUR_TEST_ADYEN_API_KEY',
            'merchantAccount': 'YOUR_TEST_MERCHANT_ACCOUNT',
        }
    }
})
```

### Production Environment

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': False,
    'providerConfig': {
        'adyen': {
            'apiKey': 'YOUR_PRODUCTION_ADYEN_API_KEY',
            'merchantAccount': 'YOUR_PRODUCTION_MERCHANT_ACCOUNT',
        }
    }
})
``` 