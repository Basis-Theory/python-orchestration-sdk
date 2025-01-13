# test_sdk.py
import os
import uuid
import pytest
from datetime import datetime, timedelta
from dotenv import load_dotenv
from basistheory.api_client import ApiClient
from basistheory.configuration import Configuration
from basistheory.api.tokens_api import TokensApi
from payment_orchestration_sdk import PaymentOrchestrationSDK
from payment_orchestration_sdk.models import (
    TransactionResponse,
    TransactionStatus,
    TransactionSource,
    TransactionStatusCode,
    RecurringType,
    ErrorCategory,
    ErrorType
)

# Load environment variables from .env file
load_dotenv()


async def create_bt_token(card_number: str = "4242424242424242"):
    """Create a Basis Theory token for testing."""
    configuration = Configuration(
        api_key=os.environ['BASISTHEORY_API_KEY']
    )
    # Calculate expiry time (10 minutes from now)
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"
    
    with ApiClient(configuration) as api_client:
        tokens_api = TokensApi(api_client)
        token = tokens_api.create({
            "type": "card",
            "data": {
                "number": card_number,
                "expiration_month": "03",
                "expiration_year": "2030",
                "cvc": "737"
            },
            "expires_at": expires_at
        })
        return token.id

async def create_bt_token_intent(card_number: str = "4242424242424242"):
    """Create a Basis Theory token for testing."""
    import requests

    url = "https://api.basistheory.com/token-intents"
    headers = {
        "BT-API-KEY": os.environ['BASISTHEORY_API_KEY'],
        "Content-Type": "application/json"
    }
    payload = {
        "type": "card",
        "data": {
            "number": card_number,
            "expiration_month": "03",
            "expiration_year": "2030",
            "cvc": "737"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    print(f"Response: {response_data}")
    return response_data['id']

@pytest.mark.asyncio
async def test_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': os.environ['BASISTHEORY_API_KEY'],
        'providerConfig': {
            'checkout': {
                'private_key': os.environ['CHECKOUT_PRIVATE_KEY'],
                'processing_channel': os.environ['CHECKOUT_PROCESSING_CHANNEL']
            }
        }
    })

    # Create a test transaction with a processor token
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.UNSCHEDULED,
        'amount': {
            'value': 100,  # Amount in cents
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': token_id,
            'store_with_provider': True,
            'holderName': 'John Doe'
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
    response = await sdk.checkout.transaction(transaction_request)
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
    print(f"Provisioned source: {response['source']['provisioned']}")
    assert isinstance(response['source']['provisioned'], dict)
    assert 'id' in response['source']['provisioned']
    
    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    
    assert 'created_at' in response
    # Optionally validate created_at is a valid datetime string
    print(f"Created at: {response['created_at']}")
    try:
        datetime.fromisoformat(response['created_at'].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("created_at is not a valid ISO datetime string")