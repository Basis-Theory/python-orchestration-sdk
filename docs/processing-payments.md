# Processing Payments

This guide explains how to process different types of payments using the Payment Orchestration SDK.

## Table of Contents

- [One-Time Payments](#one-time-payments)
- [Card-on-File Payments](#card-on-file-payments)
- [3DS Authentication](#3ds-authentication)
- [Using Token Intents](#using-token-intents)
- [Using Processor Tokens](#using-processor-tokens)

## One-Time Payments

For one-time payments where you don't want to store the card for future use:

```python
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

response = await sdk.adyen.transaction(transaction_request)
```

## Card-on-File Payments

Transact and store a card for future use with a provider (card on file):

```python
transaction_request = {
    'reference': 'unique-transaction-reference',
    'type': RecurringType.UNSCHEDULED,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': 'YOUR_BASIS_THEORY_TOKEN_ID',
        'store_with_provider': True,
        'holderName': 'John Doe'
    },
    'customer': {
        'reference': 'customer-reference',
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

response = await sdk.adyen.transaction(transaction_request)

# The response will include a provisioned source that can be used for future payments
processor_token = response['source']['provisioned']['id']
```

## 3DS Authentication

How to pass third party authentication data to a provider:

```python
transaction_request = {
    'reference': 'unique-transaction-reference',
    'type': RecurringType.ONE_TIME,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': 'YOUR_BASIS_THEORY_TOKEN_ID',
        'store_with_provider': False
    },
    'customer': {
        'reference': 'customer-reference',
    },
    'three_ds': {
        'eci': '05',
        'authentication_value': 'YOUR_3DS_AUTH_VALUE',
        'xid': 'YOUR_3DS_XID',
        'version': '2.2.0'
    }
}

response = await sdk.adyen.transaction(transaction_request)
```

## Using Basis Theory Token Intents

Transact with a token intent:

```python
# First, create a token intent
import requests

url = "https://api.basistheory.com/token-intents"
headers = {
    "BT-API-KEY": "YOUR_BASIS_THEORY_API_KEY",
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

# Then use the token intent in a transaction
transaction_request = {
    'reference': 'unique-transaction-reference',
    'type': RecurringType.ONE_TIME,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'basis_theory_token_intent',
        'id': token_intent_id,
        'store_with_provider': False
    },
    'customer': {
        'reference': 'customer-reference',
    }
}

response = await sdk.adyen.transaction(transaction_request)
```

## Using Processor Tokens

Transact with card stored with a processor (processor token):

```python
transaction_request = {
    'reference': 'unique-transaction-reference',
    'type': RecurringType.UNSCHEDULED,
    'merchant_initiated': True,
    'amount': {
        'value': 1000,
        'currency': 'USD'
    },
    'source': {
        'type': 'processor_token',
        'id': 'PREVIOUSLY_STORED_PROCESSOR_TOKEN',
    },
    'customer': {
        'reference': 'customer-reference',
    }
}

response = await sdk.adyen.transaction(transaction_request)
```

## Response Handling

All transaction responses include:

- Transaction ID and reference
- Amount and currency
- Transaction status and provider code
- Source information (including provisioned token if stored)
- Full provider response for debugging
- Network transaction ID

Example successful response:
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
        'provider_code': 'Authorised'
    },
    'source': {
        'type': 'basis_theory_token',
        'id': 'token-id',
        'provisioned': {
            'id': 'processor-token'  # Only present if store_with_provider was True
        }
    },
    'networkTransactionId': 'network-transaction-id',
    'full_provider_response': {
        # Raw provider response
    }
} 