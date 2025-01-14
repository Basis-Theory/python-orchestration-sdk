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

| Enum | Code | Description |
|------|-------|-------------|
| AUTHENTICATION_ERROR | "authentication_error" | Issues with API keys or authentication |
| PAYMENT_METHOD_ERROR | "payment_method_error" | Issues with the payment method (card expired, invalid, etc.) |
| PROCESSING_ERROR | "processing_error" | General processing errors |
| VALIDATION_ERROR | "validation_error" | Invalid request data |
| BASIS_THEORY_ERROR | "basis_theory_error" | Issues with Basis Theory services |
| FRAUD_DECLINE | "Fraud Decline" | Transactions declined due to fraud |
| OTHER | "Other" | Other unspecified errors |

## Error Types

The SDK includes the following error types:

| Enum | Code | Category | Description |
|-------|------|-----------|-------------|
| REFUSED | "refused" | PROCESSING_ERROR | The transaction was refused. |
| REFERRAL | "referral" | PROCESSING_ERROR | The issuing bank cannot automatically approve the transaction. |
| ACQUIRER_ERROR | "acquirer_error" | OTHER | The transaction did not go through due to an error that occurred on the acquirer's end. |
| BLOCKED_CARD | "blocked_card" | PAYMENT_METHOD_ERROR | The card used for the transaction is blocked, therefore unusable. |
| EXPIRED_CARD | "expired_card" | PAYMENT_METHOD_ERROR | The card used for the transaction has expired. Therefore it is unusable. |
| INVALID_AMOUNT | "invalid_amount" | OTHER | An amount mismatch occurred during the transaction process. |
| INVALID_CARD | "invalid_card" | PAYMENT_METHOD_ERROR | The specified card number is incorrect or invalid. |
| INVALID_SOURCE_TOKEN | "invalid_source_token" | PAYMENT_METHOD_ERROR | The provided source token (processor token) is invalid or expired. |
| OTHER | "other" | OTHER | This response maps all those response codes that cannot be reliably mapped. |
| NOT_SUPPORTED | "not_supported" | PROCESSING_ERROR | The shopper's bank does not support or does not allow this type of transaction. |
| AUTHENTICATION_FAILURE | "authentication_failure" | PAYMENT_METHOD_ERROR | The 3D Secure authentication failed due to an issue at the card network or issuer. |
| INSUFFICENT_FUNDS | "insufficient_funds" | PAYMENT_METHOD_ERROR | The card does not have enough money to cover the payable amount. |
| FRAUD | "fraud" | FRAUD_DECLINE | Possible fraud. |
| PAYMENT_CANCELLED | "payment_cancelled" | OTHER | The transaction was cancelled. |
| PAYMENT_CANCELLED_BY_CONSUMER | "payment_cancelled_by_consumer" | PROCESSING_ERROR | The shopper cancelled the transaction before completing it. |
| INVALID_PIN | "invalid_pin" | PAYMENT_METHOD_ERROR | The specified PIN is incorrect or invalid. |
| PIN_TRIES_EXCEEDED | "pin_tries_exceeded" | PAYMENT_METHOD_ERROR | The shopper specified an incorrect PIN more that three times in a row. |
| CVC_INVALID | "cvc_invalid" | PAYMENT_METHOD_ERROR | The specified CVC (card security code) is invalid. |
| RESTRICTED_CARD | "restricted_card" | PROCESSING_ERROR | The card is restricted from making this type of transaction. |
| STOP_PAYMENT | "stop_payment" | PROCESSING_ERROR | Indicates that the shopper requested to stop a subscription. |
| AVS_DECLINE | "avs_decline" | PROCESSING_ERROR | The address data the shopper entered is incorrect. |
| PIN_REQUIRED | "pin_required" | PROCESSING_ERROR | A PIN is required to complete the transaction. |
| BANK_ERROR | "bank_error" | PROCESSING_ERROR | An error occurred with the shopper's bank during processing. |
| CONTACTLESS_FALLBACK | "contactless_fallback" | PROCESSING_ERROR | The shopper abandoned the transaction after they attempted a contactless payment. |
| AUTHENTICATION_REQUIRED | "authentication_required" | PROCESSING_ERROR | The issuer requires authentication for the transaction. Retry with 3D Secure. |
| PROCESSOR_BLOCKED | "processor_blocked" | PROCESSING_ERROR | Transaction blocked by Adyen's excessive retry prevention service. |
| INVALID_API_KEY | "invalid_api_key" | AUTHENTICATION_ERROR | The API key provided is invalid. |
| UNAUTHORIZED | "unauthorized" | AUTHENTICATION_ERROR | The request is not authorized to access the resource. |
| CONFIGURATION_ERROR | "configuration_error" | OTHER | An error occurred in the configuration settings. |
| BT_UNAUTHENTICATED | "unauthenticated" | BASIS_THEORY_ERROR | Authentication failed with Basis Theory. |
| BT_UNAUTHORIZED | "unauthorized" | BASIS_THEORY_ERROR | Request not authorized with Basis Theory. |
| BT_REQUEST_ERROR | "request_error" | BASIS_THEORY_ERROR | Error occurred during Basis Theory API request. |
| BT_UNEXPECTED | "unexpected" | BASIS_THEORY_ERROR | Unexpected error occurred with Basis Theory. |

## Example Error Scenarios

### Expired Card

```python
try:
    response = await sdk.adyen.transaction(transaction_request)
except Exception as e:
    # Error response will look like:
    {
        'error_codes': [{
            'category': 'payment_method_error',
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

1. Use the provider errors array for detailed error messages
2. Log the full provider response for debugging purposes
3. Handle common error categories with appropriate user messaging