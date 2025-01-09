# test_sdk.py
import os
import pytest
from dotenv import load_dotenv
from payment_orchestration_sdk import PaymentOrchestrationSDK

# Load environment variables from .env file
load_dotenv()

@pytest.mark.asyncio
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
        'reference': 'test_payment_123',  # Unique reference for the transaction
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': '46f2f39e-6c33-457c-a64e-292c55c2ddc9',  # Replace with a real stored payment method ID
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

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    assert response is not None  # Add more specific assertions based on expected response
