# Adyen Provider

This guide explains how to use Adyen as a payment provider with the Payment Orchestration SDK.

## Configuration

Configure Adyen in the SDK initialization, for additional information on initializing the SDK see the [API Reference](../api-reference.md#sdk-initialization).

```python
sdk = PaymentOrchestrationSDK.init({
    'is_test': True,  # Set to False for production
    'bt_api_key': os.getenv('BASISTHEORY_API_KEY'),
    'provider_config': {
        'adyen': {
            'api_key': os.getenv('ADYEN_API_KEY'),
            'merchant_account': os.getenv('ADYEN_MERCHANT_ACCOUNT'),
            'production_prefix': os.getenv('ADYEN_PRODUCTION_PREFIX')
        }
    }
})
```

## Required Credentials

| Credential | Property Name | Description |
|------------|--------------|-------------|
| Adyen API Key | api_key | Your Adyen API key for authentication |
| Merchant Account | merchant_account | Your Adyen merchant account identifier |
| Production Prefix | production_prefix | Your Adyen production prefix |


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

### Adyen Additional Data

You can override any provider properties by passing the `override_provider_properties` property in the [TransactionRequest](../api-reference.md#transactionrequest) model. For example, to utilize [Adyen's Additional Data](https://docs.adyen.com/api-explorer/Checkout/latest/post/payments#request-additionalData), you can pass the following:

```python
override_provider_properties = {
    "additionalData": {
        "riskdata.userStatus": "userStatusTest",
        "enhancedSchemeData.customerReference": "customerReferenceTest",
        "autoRescue": "true",
        "enhancedSchemeData.totalTaxAmount": "totalTaxAmountTest"
    }
}
```