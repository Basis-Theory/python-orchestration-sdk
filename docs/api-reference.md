# API Reference

Complete reference for the Payment Orchestration SDK.

## SDK Initialization

### PaymentOrchestrationSDK.init

Initialize the SDK with configuration options.

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': bool,
    'btApiKey': str,
    'providerConfig': {
        'adyen': {
            'apiKey': str,
            'merchantAccount': str,
        }
    }
})
```

## Transaction Methods

Process a payment transaction through a provider, find all of the providers available in our [Providers](./providers/index.md) documentation. Each provider uses the same method signature, request model, and response model. Keep in mind - Each provider may have a unique combination of these fields to accomplish the same goal (e.g. Charging a card-on-file for a subscription vs a customer initiated transaction for two different providers).

```python
sdk.[provider].transaction(transaction_request)
```

#### Parameters

- `transaction_request`: Dictionary containing:
  - `reference`: str - Unique transaction reference
  - `type`: RecurringType - Transaction type
  - `amount`: Amount - Transaction amount
  - `source`: Source - Payment source
  - `customer`: Customer (optional) - Customer information
  - `three_ds`: ThreeDS (optional) - 3DS authentication data
  - `merchant_initiated`: bool (optional) - Whether the transaction is merchant-initiated

## Data Models

### RecurringType

```python
class RecurringType(str, Enum):
    ONE_TIME = "ONE_TIME"
    CARD_ON_FILE = "CARD_ON_FILE"
    SUBSCRIPTION = "SUBSCRIPTION"
    UNSCHEDULED = "UNSCHEDULED"
```

### SourceType

```python
class SourceType(str, Enum):
    BASIS_THEORY_TOKEN = "basis_theory_token"
    BASIS_THEORY_TOKEN_INTENT = "basis_theory_token_intent"
    PROCESSOR_TOKEN = "processor_token"
```

### Amount

```python
@dataclass
class Amount:
    value: int  # Amount in cents
    currency: str = "USD"
```

### Source

```python
@dataclass
class Source:
    type: SourceType
    id: str
    store_with_provider: bool = False
    holderName: Optional[str] = None
```

### Customer

```python
@dataclass
class Customer:
    reference: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Address] = None
```

### Address

```python
@dataclass
class Address:
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
```

### ThreeDS

```python
@dataclass
class ThreeDS:
    eci: Optional[str] = None
    authentication_value: Optional[str] = None
    xid: Optional[str] = None
    version: Optional[str] = None
```

### TransactionStatus

```python
class TransactionStatusCode(str, Enum):
    AUTHORIZED = "Authorized"
    PENDING = "Pending"
    CARD_VERIFIED = "Card Verified"
    DECLINED = "Declined"
    RETRY_SCHEDULED = "Retry Scheduled"
    CANCELLED = "Cancelled"
    CHALLENGE_SHOPPER = "ChallengeShopper"
    RECEIVED = "Received"
    PARTIALLY_AUTHORIZED = "PartiallyAuthorised"
```

## Response Models

### TransactionResponse

```python
@dataclass
class TransactionResponse:
    id: str
    reference: str
    amount: Amount
    status: TransactionStatus
    source: TransactionSource
    full_provider_response: Dict[str, Any]
    created_at: datetime
    networkTransactionId: Optional[str] = None
```

### ErrorResponse

```python
@dataclass
class ErrorResponse:
    error_codes: list[ErrorCode]
    provider_errors: list[str]
    full_provider_response: Dict[str, Any]
```

### ErrorCode

```python
@dataclass
class ErrorCode:
    category: str
    code: str
```

## Error Categories

```python
class ErrorCategory(str, Enum):
    AUTHENTICATION_ERROR = "authentication_error"
    PAYMENT_METHOD_ERROR = "payment_method_error"
    PROCESSING_ERROR = "processing_error"
    VALIDATION_ERROR = "validation_error"
    BASIS_THEORY_ERROR = "basis_theory_error"
    FRAUD_DECLINE = "Fraud Decline"
    OTHER = "Other"
```

## Error Types

See [Error Handling](./error-handling.md#error-types) for the complete list of error types. 