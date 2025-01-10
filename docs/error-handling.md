# Error Handling

The Payment Orchestration SDK provides comprehensive error handling with standardized error categories and codes across different payment providers.

## Error Response Structure

When a transaction fails, the SDK returns an error response with the following structure:

```python
{
    'error_codes': [
        {
            'category': 'payment_method_error',
            'code': 'expired_card'
        }
    ],
    'provider_errors': [
        'Expired Card'
    ],
    'full_provider_response': {
        # Raw provider response
    }
}
```

## Error Categories

The SDK standardizes errors into the following categories:

- `authentication_error`: Issues with API keys or authentication
- `payment_method_error`: Issues with the payment method (card expired, invalid, etc.)
- `processing_error`: General processing errors
- `validation_error`: Invalid request data
- `basis_theory_error`: Issues with Basis Theory services
- `fraud_decline`: Transactions declined due to fraud
- `other`: Other unspecified errors

## Error Types

The SDK includes the following error types:

```python
class ErrorType(Enum):
    REFUSED = ("refused", ErrorCategory.PROCESSING_ERROR)
    REFERRAL = ("referral", ErrorCategory.PROCESSING_ERROR)
    ACQUIRER_ERROR = ("acquirer_error", ErrorCategory.OTHER)
    BLOCKED_CARD = ("blocked_card", ErrorCategory.PAYMENT_METHOD_ERROR)
    EXPIRED_CARD = ("expired_card", ErrorCategory.PAYMENT_METHOD_ERROR)
    INVALID_AMOUNT = ("invalid_amount", ErrorCategory.OTHER)
    INVALID_CARD = ("invalid_card", ErrorCategory.PAYMENT_METHOD_ERROR)
    OTHER = ("other", ErrorCategory.OTHER)
    NOT_SUPPORTED = ("not_supported", ErrorCategory.PROCESSING_ERROR)
    AUTHENTICATION_FAILURE = ("authentication_failure", ErrorCategory.PAYMENT_METHOD_ERROR)
    INSUFFICENT_FUNDS = ("insufficient_funds", ErrorCategory.PAYMENT_METHOD_ERROR)
    FRAUD = ("fraud", ErrorCategory.FRAUD_DECLINE)
    PAYMENT_CANCELLED = ("payment_cancelled", ErrorCategory.OTHER)
    PAYMENT_CANCELLED_BY_CONSUMER = ("payment_cancelled_by_consumer", ErrorCategory.PROCESSING_ERROR)
    INVALID_PIN = ("invalid_pin", ErrorCategory.PAYMENT_METHOD_ERROR)
    PIN_TRIES_EXCEEDED = ("pin_tries_exceeded", ErrorCategory.PAYMENT_METHOD_ERROR)
    CVC_INVALID = ("cvc_invalid", ErrorCategory.PAYMENT_METHOD_ERROR)
    RESTRICTED_CARD = ("restricted_card", ErrorCategory.PROCESSING_ERROR)
    STOP_PAYMENT = ("stop_payment", ErrorCategory.PROCESSING_ERROR)
    AVS_DECLINE = ("avs_decline", ErrorCategory.PROCESSING_ERROR)
    PIN_REQUIRED = ("pin_required", ErrorCategory.PROCESSING_ERROR)
    BANK_ERROR = ("bank_error", ErrorCategory.PROCESSING_ERROR)
    CONTACTLESS_FALLBACK = ("contactless_fallback", ErrorCategory.PROCESSING_ERROR)
    AUTHENTICATION_REQUIRED = ("authentication_required", ErrorCategory.PROCESSING_ERROR)
    PROCESSOR_BLOCKED = ("processor_blocked", ErrorCategory.PROCESSING_ERROR)
    INVALID_API_KEY = ("invalid_api_key", ErrorCategory.AUTHENTICATION_ERROR)
    UNAUTHORIZED = ("unauthorized", ErrorCategory.AUTHENTICATION_ERROR)
    BT_UNAUTHENTICATED = ("unauthenticated", ErrorCategory.BASIS_THEORY_ERROR)
    BT_UNAUTHORIZED = ("unauthorized", ErrorCategory.BASIS_THEORY_ERROR)
    BT_REQUEST_ERROR = ("request_error", ErrorCategory.BASIS_THEORY_ERROR)
    BT_UNEXPECTED = ("unexpected", ErrorCategory.BASIS_THEORY_ERROR)
```
## Example Error Scenarios

### Expired Card

```python
try:
    response = await sdk.adyen.transaction(transaction_request)
except Exception as e:
    # Error response will look like:
    {
        'error_codes': [{
            'category': ErrorCategory.PAYMENT_METHOD_ERROR,
            'code': 'expired_card'
        }],
        'provider_errors': ['Expired Card'],
        'full_provider_response': {
            'resultCode': 'Refused',
            'refusalReason': 'Expired Card',
            'refusalReasonCode': '6'
        }
    }
```

## Best Practices

1. Always check for both the error category and specific error code
2. Use the provider errors array for detailed error messages
3. Log the full provider response for debugging purposes
4. Handle common error categories with appropriate user messaging