# Checkout.com Provider

This guide explains how to use Checkout.com as a payment provider with the Payment Orchestration SDK.

## Configuration

Configure Checkout.com in the SDK initialization, for additional information on initializing the SDK see the [API Reference](../api-reference.md#sdk-initialization).

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

For testing, a few test card numbers are provided below, for a full list of test cards see the [Checkout.com documentation](https://www.checkout.com/docs/developer-resources/testing/test-cards).

| Card Type | Number | Notes |
|-----------|---------|-------|
| Visa | 4242424242424242 | Standard test card |
| Mastercard | 5555555555554444 | Standard test card |
| American Express | 378282246310005 | Standard test card |

## Transactions

You will use the `sdk.checkout.transaction()` method to process transactions following the [TransactionRequest](../api-reference.md#transactionrequest) model.