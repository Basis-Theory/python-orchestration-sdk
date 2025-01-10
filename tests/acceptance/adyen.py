# test_sdk.py
import os
import pytest
from datetime import datetime
from dotenv import load_dotenv
from payment_orchestration_sdk import PaymentOrchestrationSDK
from payment_orchestration_sdk.models import TransactionResponse, TransactionStatus, TransactionSource, TransactionThreeDS

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
    
    # Validate response structure
    assert isinstance(response, dict)
    assert 'id' in response
    assert 'reference' in response
    assert response['reference'] == transaction_request['reference']
    
    # Validate amount
    assert 'amount' in response
    assert isinstance(response['amount'], dict)
    assert 'value' in response['amount']
    assert 'currency' in response['amount']
    assert response['amount']['currency'] == 'USD'
    
    # Validate status
    assert 'status' in response
    assert isinstance(response['status'], dict)
    assert 'code' in response['status']
    assert response['status']['code'] == 'Authorized'
    assert 'provider_code' in response['status']
    

    # # Validate 3DS if present
    # if 'three_ds' in response:
    #     assert isinstance(response['three_ds'], dict)
    #     assert 'downgraded' in response['three_ds']
    #     assert isinstance(response['three_ds']['downgraded'], bool)
    #     if 'enrolled' in response['three_ds']:
    #         assert isinstance(response['three_ds']['enrolled'], str)
    #     if 'eci' in response['three_ds']:
    #         assert isinstance(response['three_ds']['eci'], str)
    
    # Validate source
    assert 'source' in response
    assert isinstance(response['source'], dict)
    assert 'type' in response['source']
    assert response['source']['type'] in ['basis_theory_token']
    assert 'id' in response['source']
    # if 'provisioned' in response['source']:
    #     assert isinstance(response['source']['provisioned'], dict)
    #     assert 'id' in response['source']['provisioned']
    
    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    
    assert 'created_at' in response
    # Optionally validate created_at is a valid datetime string
    try:
        datetime.fromisoformat(response['created_at'].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("created_at is not a valid ISO datetime string")
