# Adyen Provider

This guide explains how to use Adyen as a payment provider with the Payment Orchestration SDK.

## Configuration

Configure Adyen in the SDK initialization, for additional information on initializing the SDK see the [API Reference](../api-reference.md#sdk-initialization).

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,  # Set to False for production
    'btApiKey': os.getenv('BASISTHEORY_API_KEY'),
    'providerConfig': {
        'adyen': {
            'apiKey': os.getenv('ADYEN_API_KEY'),
            'merchantAccount': os.getenv('ADYEN_MERCHANT_ACCOUNT'),
            'productionPrefix': os.getenv('ADYEN_PRODUCTION_PREFIX')
        }
    }
})
```

## Required Credentials

| Credential | Property Name | Description |
|------------|--------------|-------------|
| Adyen API Key | apiKey | Your Adyen API key for authentication |
| Merchant Account | merchantAccount | Your Adyen merchant account identifier |
| Production Prefix | productionPrefix | Your Adyen production prefix |


You can obtain these credentials from your [Adyen Customer Area](https://ca-test.adyen.com/ca/ca/overview/default.shtml).

## Test Cards

For testing, a few test card numbers are provided below, for a full list of test cards see the [Adyen Test Cards](https://docs.adyen.com/development-resources/testing/test-card-numbers/) and [Adyen Failure Cards](https://docs.adyen.com/development-resources/testing/result-codes/#values-for-testing-result-reasons).

| Card Type | Number | Notes |
|-----------|---------|-------|
| Regular Card | 4111111145551142 | Standard test card |
| 3DS Card | 4917610000000000 | Card that triggers 3DS flow |
| Expired Card | Any valid card number | Use with `holderName: "CARD_EXPIRED"` |

## Transactions

You will use the `sdk.adyen.transaction()` method to process transactions following the [TransactionRequest](../api-reference.md#transactionrequest) model.