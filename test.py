# test_sdk.py
import os
import asyncio
from payment_orchestration_sdk import PaymentOrchestrationSDK


async def test_processor_token_payment():
    # Initialize the SDK with environment variables
    sdk = PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': os.environ['BASISTHEORY_API_KEY'],
        'providerConfig': {
            'adyen': {
                'apiKey': os.environ['ADYEN_API_KEY'],
                'merchantAccount': os.environ['ADYEN_MERCHANT_ACCOUNT'],
            }
        }
    })

    # Create a test transaction with a processor token
    transaction_request = {
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': '05e81aed-7ced-46a9-a814-80ec9ba744cb',  # Replace with a real stored payment method ID
            'store_with_provider': False
        },
        'customer': {
            'reference': 'customer_test_123',
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

    try:
        # Make the transaction request
        print("Making transaction request...")
        response = await sdk.adyen.transaction(transaction_request)
        print("\nTransaction Response:")
        print(response)

    except Exception as e:
        print(f"\nError occurred: {str(e)}")


# Run the test
if __name__ == "__main__":
    asyncio.run(test_processor_token_payment())
