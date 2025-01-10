# test_sdk.py
import os
import uuid
import pytest
from datetime import datetime
from dotenv import load_dotenv
from payment_orchestration_sdk import PaymentOrchestrationSDK
from payment_orchestration_sdk.models import (
    TransactionResponse,
    TransactionStatus,
    TransactionSource,
    TransactionStatusCode,
    RecurringType
)

# Load environment variables from .env file
load_dotenv()

@pytest.mark.asyncio
async def test_storing_card_on_file():
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
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.CARD_ON_FILE,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': '46f2f39e-6c33-457c-a64e-292c55c2ddc9',  # Replace with a real stored payment method ID
            'store_with_provider': True
        },
        'customer': {
            'reference': str(uuid.uuid4()),
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
    print(f"Response: {response['full_provider_response']}")

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
    assert response['status']['code'] == TransactionStatusCode.AUTHORIZED
    assert 'provider_code' in response['status']
    
    # Validate source
    assert 'source' in response
    assert isinstance(response['source'], dict)
    assert 'type' in response['source']
    assert response['source']['type'] in ['basis_theory_token']
    assert 'id' in response['source']
    # if 'provisioned' in response['source']:
    print(f"Provisioned source: {response['source']['provisioned']}")
    assert isinstance(response['source']['provisioned'], dict)
    assert 'id' in response['source']['provisioned']
    
    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    
    assert 'created_at' in response
    # Optionally validate created_at is a valid datetime string
    try:
        datetime.fromisoformat(response['created_at'].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("created_at is not a valid ISO datetime string")

    # Validate networkTransactionId
    assert 'networkTransactionId' in response
    assert isinstance(response['networkTransactionId'], str)
    assert len(response['networkTransactionId']) > 0


@pytest.mark.asyncio
async def test_not_storing_card_on_file():
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
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
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
            'reference': str(uuid.uuid4()),
        }
    }

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response['full_provider_response']}")

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
    assert response['status']['code'] == TransactionStatusCode.AUTHORIZED
    assert 'provider_code' in response['status']
    
    # Validate source
    assert 'source' in response
    assert isinstance(response['source'], dict)
    assert 'type' in response['source']
    assert response['source']['type'] in ['basis_theory_token']
    assert 'id' in response['source']
    assert response['source']['provisioned'] == None

    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)

    # Validate networkTransactionId
    assert 'networkTransactionId' in response
    assert isinstance(response['networkTransactionId'], str)
    assert len(response['networkTransactionId']) > 0

@pytest.mark.asyncio
async def test_with_three_ds():
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
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': '16264335-b209-4277-a3ea-f04a95ec0b88',  # Replace with a real stored payment method ID
            'store_with_provider': False
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        },
        'three_ds': {
            'eci': '05',
            'authentication_value': 'AAABCZIhcQAAAABZlyFxAAAAAAA=',
            'xid': 'AAABCZIhcQAAAABZlyFxAAAAAAA=',
            'version': '2.2.0'
        }
    }

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response['full_provider_response']}")

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
    assert response['status']['code'] == TransactionStatusCode.AUTHORIZED
    assert 'provider_code' in response['status']
    
    # Validate source
    assert 'source' in response
    assert isinstance(response['source'], dict)
    assert 'type' in response['source']
    assert response['source']['type'] in ['basis_theory_token']
    assert 'id' in response['source']
    assert response['source']['provisioned'] == None

    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)

    # Validate networkTransactionId
    assert 'networkTransactionId' in response
    assert isinstance(response['networkTransactionId'], str)
    assert len(response['networkTransactionId']) > 0
