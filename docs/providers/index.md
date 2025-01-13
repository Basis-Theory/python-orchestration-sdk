# Payment Providers

The Payment Orchestration SDK supports multiple payment providers. Each provider has its own specific configuration and features, but they all follow the same standardized interface for ease of use.

## Available Providers

- [Adyen](./adyen.md)
- [Checkout.com](./checkout.md)

## Common Features

All providers support:

- One-time payments
- Card-on-file payments
- 3DS authentication
- Error handling and standardization
- Token management

## Provider Selection

When choosing a provider, consider:

1. **Geographic Coverage**: Some providers have better coverage in certain regions
2. **Pricing**: Fee structures vary between providers
3. **Features**: Some providers offer specialized features
4. **Integration Complexity**: Some providers require more setup than others

## Adding a Provider

To use a provider:

1. Sign up for an account with the provider
2. Obtain API credentials
3. Configure the SDK with your credentials:

```python
sdk = PaymentOrchestrationSDK.init({
    'isTest': True,
    'btApiKey': 'YOUR_BASIS_THEORY_API_KEY',
    'providerConfig': {
        'provider_name': {
            # Provider-specific configuration
        }
    }
})
```

## Provider-Specific Documentation

Each provider has its own documentation page with:

- Configuration details
- Test card numbers
- Provider-specific features
- Error code mappings
- Environment setup

Select a provider from the list above to view its detailed documentation.