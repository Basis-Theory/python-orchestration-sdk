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

| ENUM | Description |
|------|-------------|
| AUTHENTICATION_ERROR | Issues with API keys or authentication |
| PAYMENT_METHOD_ERROR | Issues with the payment method (card expired, invalid, etc.) |
| PROCESSING_ERROR | General processing errors |
| VALIDATION_ERROR | Invalid request data |
| BASIS_THEORY_ERROR | Issues with Basis Theory services |
| FRAUD_DECLINE | Transactions declined due to fraud |
| OTHER | Other unspecified errors |

## Error Types

The SDK includes the following error types:

| Error | Category | Description |
|-------|-----------|-------------|
| REFUSED | PROCESSING_ERROR | The transaction was refused. |
| REFERRAL | PROCESSING_ERROR | The issuing bank cannot automatically approve the transaction. |
| ACQUIRER_ERROR | OTHER | The transaction did not go through due to an error that occurred on the acquirer's end. |
| BLOCKED_CARD | PAYMENT_METHOD_ERROR | The card used for the transaction is blocked, therefore unusable. |
| EXPIRED_CARD | PAYMENT_METHOD_ERROR | The card used for the transaction has expired. Therefore it is unusable. |
| INVALID_AMOUNT | OTHER | An amount mismatch occurred during the transaction process. |
| INVALID_CARD | PAYMENT_METHOD_ERROR | The specified card number is incorrect or invalid. |
| INVALID_SOURCE_TOKEN | PAYMENT_METHOD_ERROR | The provided source token (processor token) is invalid or expired. |
| OTHER | OTHER | This response maps all those response codes that cannot be reliably mapped. |
| NOT_SUPPORTED | PROCESSING_ERROR | The shopper's bank does not support or does not allow this type of transaction. |
| AUTHENTICATION_FAILURE | PAYMENT_METHOD_ERROR | The 3D Secure authentication failed due to an issue at the card network or issuer. |
| INSUFFICENT_FUNDS | PAYMENT_METHOD_ERROR | The card does not have enough money to cover the payable amount. |
| FRAUD | FRAUD_DECLINE | Possible fraud. |
| PAYMENT_CANCELLED | OTHER | The transaction was cancelled. |
| PAYMENT_CANCELLED_BY_CONSUMER | PROCESSING_ERROR | The shopper cancelled the transaction before completing it. |
| INVALID_PIN | PAYMENT_METHOD_ERROR | The specified PIN is incorrect or invalid. |
| PIN_TRIES_EXCEEDED | PAYMENT_METHOD_ERROR | The shopper specified an incorrect PIN more that three times in a row. |
| CVC_INVALID | PAYMENT_METHOD_ERROR | The specified CVC (card security code) is invalid. |
| RESTRICTED_CARD | PROCESSING_ERROR | The card is restricted from making this type of transaction. |
| STOP_PAYMENT | PROCESSING_ERROR | Indicates that the shopper requested to stop a subscription. |
| AVS_DECLINE | PROCESSING_ERROR | The address data the shopper entered is incorrect. |
| PIN_REQUIRED | PROCESSING_ERROR | A PIN is required to complete the transaction. |
| BANK_ERROR | PROCESSING_ERROR | An error occurred with the shopper's bank during processing. |
| CONTACTLESS_FALLBACK | PROCESSING_ERROR | The shopper abandoned the transaction after they attempted a contactless payment. |
| AUTHENTICATION_REQUIRED | PROCESSING_ERROR | The issuer requires authentication for the transaction. Retry with 3D Secure. |
| PROCESSOR_BLOCKED | PROCESSING_ERROR | Transaction blocked by Adyen's excessive retry prevention service. |
| INVALID_API_KEY | AUTHENTICATION_ERROR | The API key provided is invalid. |
| UNAUTHORIZED | AUTHENTICATION_ERROR | The request is not authorized to access the resource. |
| CONFIGURATION_ERROR | OTHER | An error occurred in the configuration settings. |
| BT_UNAUTHENTICATED | BASIS_THEORY_ERROR | Authentication failed with Basis Theory. |
| BT_UNAUTHORIZED | BASIS_THEORY_ERROR | Request not authorized with Basis Theory. |
| BT_REQUEST_ERROR | BASIS_THEORY_ERROR | Error occurred during Basis Theory API request. |
| BT_UNEXPECTED | BASIS_THEORY_ERROR | Unexpected error occurred with Basis Theory. |

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