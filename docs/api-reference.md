# API Reference

Complete reference for the Payment Orchestration SDK.

## SDK Initialization

Initialize the SDK with configuration options.

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': bool,
    'btApiKey': str,
    'providerConfig': {
        [provider]: <ProviderConfig>
    }
})
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| isTest | bool | Yes | - | Whether to use the test environment for the provider |
| btApiKey | str | Yes | - | Basis Theory API key |
| providerConfig | Dict[str, ProviderConfig] | Yes | - | Configuration for the payment provider |

## Transaction Methods

Process a payment transaction through a provider, find all of the providers available in our [Providers](./providers/index.md) documentation. Each provider uses the same method signature, request model, and response model. Keep in mind - Each provider may have a unique combination of these fields to accomplish the same goal (e.g. Charging a card-on-file for a subscription vs a customer initiated transaction for two different providers).

```python
await sdk.[provider].transaction({
    'reference': 'merchant-reference-123', 
    'type': RecurringType.UNSCHEDULED,    
    'merchant_initiated': True,    
    'amount': {
        'value': 1000,                      
        'currency': 'USD',                 
    },       
    'source': {
        'type': 'basis_theory_token',      
        'id': 'bt_123abc...',              
        'store_with_provider': True,       
        'holderName': 'John Doe',          
    },
    'customer': {
        'reference': 'customer-123',       
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'address': {
            'address_line1': '123 Main St',
            'address_line2': 'Apt 4B',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001',
            'country': 'US' 
        },
    },
    'three_ds': {
        'eci': '05',                       
        'authentication_value': 'AAABCZIhcQAAAABZlyFxAAAAAAA=',  
        'xid': 'MDAwMDAwMDAwMDAwMDAwMDAwMDE=',                  
        'version': '2.2.0',               
    },
    'override_provider_properties': {
        'additionalData": {
            'risdata.userStatus': 'PGWC-123-TEST'
        }
    }
})
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| reference | str | Yes | - | Unique transaction reference |
| type | RecurringType | Yes | - | Transaction type |
| amount | Amount | Yes | - | Transaction amount |
| source | Source | Yes | - | Payment source |
| customer | Customer | No | None | Customer information |
| three_ds | ThreeDS | No | None | 3DS authentication data |
| merchant_initiated | bool | No | False | Whether the transaction is merchant-initiated |
| previous_network_transaction_id | str | No | None | Previous network transaction ID |
| override_provider_properties | Dict[str, Any] | No | None | Appends and replaces any pre-mapped provider properties in the provider request |
| metadata | Dict[str, Any] | No | None | Metadata to be associated with the transaction |

### Response

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| id | str | None | Unique identifier for the transaction |
| reference | str | None | Reference identifier provided in the request |
| amount | Amount | None | Amount details of the transaction |
| status | TransactionStatus | None | Current status of the transaction |
| source | TransactionSource | None | Source payment method details |
| fullProviderResponse | Dict[str, Any] | None | Complete response from the payment provider |
| createdt | datetime | None | Timestamp when transaction was created |
| network_transaction_id | str | None | Network transaction identifier |


## Request Models

### RecurringType

| Value | Description |
|-------|-------------|
| ONE_TIME | A one-time payment that will not be stored for future use |
| CARD_ON_FILE | A payment where the card details will be stored for future use |
| SUBSCRIPTION | A recurring payment on a fixed schedule (e.g. monthly subscription) |
| UNSCHEDULED | A recurring payment without a fixed schedule (e.g. top-ups) |

### SourceType

| Value | Description |
|-------|-------------|
| BASIS_THEORY_TOKEN | A Basis Theory token containing card details |
| BASIS_THEORY_TOKEN_INTENT | A Basis Theory token intent for collecting card details |
| PROCESSOR_TOKEN | A token from a payment processor containing stored card details |

### Amount

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| value | int | - | Amount in cents |
| currency | str | "USD" | Three-letter currency code |

### Source

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| type | SourceType | - | Type of payment source (BASIS_THEORY_TOKEN, BASIS_THEORY_TOKEN_INTENT, or PROCESSOR_TOKEN) |
| id | str | - | Identifier for the payment source |
| store_with_provider | bool | False | Whether to store the payment source with the provider for future use |
| holder_name | str | None | Name of the card holder |

### Customer

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| reference | str | None | Customer reference identifier |
| first_name | str | None | Customer's first name |
| last_name | str | None | Customer's last name |
| email | str | None | Customer's email address |
| address | Address | None | Customer's address details |

### Address

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| address_line1 | str | None | First line of the address |
| address_line2 | str | None | Second line of the address |
| city | str | None | City name |
| state | str | None | State/province code |
| zip | str | None | Postal/ZIP code |
| country | str | None | Two-letter country code |

### ThreeDS

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| eci | str | None | Electronic Commerce Indicator value from 3DS authentication |
| authentication_value | str | None | Authentication value/CAVV from 3DS authentication |
| xid | str | None | Transaction identifier from 3DS authentication |
| version | str | None | Version of 3DS protocol used (e.g. "2.2.0") |


## Response Models

### TransactionSource

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| type | str | None | Type of the payment source |
| id | str | None | Identifier for the payment source |
| provisioned | ProvisionedSource | None | Details of the provisioned source |

### ProvisionedSource

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| id | str | None | Identifier for the provisioned source |

### TransactionStatus

| Value | Description |
|-------|-------------|
| AUTHORIZED | Transaction was successfully authorized |
| PENDING | Transaction is pending completion |
| CARD_VERIFIED | Card was successfully verified |
| DECLINED | Transaction was declined |
| RETRY_SCHEDULED | Transaction failed but retry is scheduled |
| CANCELLED | Transaction was cancelled |
| CHALLENGE_SHOPPER | Additional shopper authentication required |
| RECEIVED | Transaction request was received |
| PARTIALLY_AUTHORIZED | Transaction was partially authorized |

## Error Handling

See [Error Handling](./error-handling.md) for details on how to handle errors.