# test_sdk.py
import os
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from basistheory.api_client import ApiClient # type: ignore
from basistheory.configuration import Configuration # type: ignore
from basistheory.api.tokens_api import TokensApi # type: ignore
from orchestration_sdk import PaymentOrchestrationSDK
from orchestration_sdk.models import (
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

async def create_bt_token(card_number: str = "4111111145551142"):
    """Create a Basis Theory token for testing."""
    configuration = Configuration(
        api_key=os.getenv('BASISTHEORY_API_KEY')
    )
    # Calculate expiry time (10 minutes from now)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    
    with ApiClient(configuration) as api_client:
        tokens_api = TokensApi(api_client)
        token = tokens_api.create({
            "type": "card",
            "data": {
                "number": card_number,
                "expiration_month": "03",
                "expiration_year": "2030",
                "cvc": 737
            },
            "expires_at": expires_at
        })
        return token.id

async def create_bt_token_intent(card_number: str = "4111111145551142"):
    """Create a Basis Theory token for testing."""
    import requests

    url = "https://api.basistheory.com/token-intents"
    headers = {
        "BT-API-KEY": os.getenv('BASISTHEORY_API_KEY'),
        "Content-Type": "application/json"
    }
    payload = {
        "type": "card",
        "data": {
            "number": card_number,
            "expiration_month": "03",
            "expiration_year": "2030",
            "cvc": 737
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    print(f"Response: {response_data}")
    return response_data['id']

def get_sdk(api_key = os.getenv('ADYEN_API_KEY'), merchant_account = os.getenv('ADYEN_MERCHANT_ACCOUNT')):
    return PaymentOrchestrationSDK.init({
        'is_test': True,
        'bt_api_key': os.getenv('BASISTHEORY_API_KEY'),
        'provider_config': {
            'adyen': {
                'api_key': api_key,
                'merchant_account': merchant_account,
            }
        }
    })

@pytest.mark.asyncio
async def test_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.UNSCHEDULED,
        'amount': {
            'value': 2000,  # Amount in cents (20.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': token_id,
            'store_with_provider': True,
            'holder_name': 'John Doe'
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
        },
        'metadata': {
            'order_id': '12345',
            'customer_reference': 'cust_123'
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
    print(f"Provisioned source: {response['source']['provisioned']}")
    assert isinstance(response['source']['provisioned'], dict)
    assert 'id' in response['source']['provisioned']
    
    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    
    assert 'created_at' in response
    # Validate created_at is a valid datetime string
    try:
        # Remove any duplicate timezone offset
        created_at = response['created_at']
        if '+00:00+00:00' in created_at:
            created_at = created_at.replace('+00:00+00:00', '+00:00')
        print(f"Created at: {created_at}")
        datetime.fromisoformat(created_at)
    except ValueError:
        pytest.fail("created_at is not a valid ISO datetime string")

    # Validate networkTransactionId
    assert 'network_transaction_id' in response
    assert isinstance(response['network_transaction_id'], str)
    assert len(response['network_transaction_id']) > 0

@pytest.mark.asyncio
async def test_not_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk(); 

    
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': token_id,
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
    assert 'network_transaction_id' in response
    assert isinstance(response['network_transaction_id'], str)
    assert len(response['network_transaction_id']) > 0

@pytest.mark.asyncio
async def test_with_three_ds():
    # Create a Basis Theory token
    token_id = await create_bt_token("4917610000000000")

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': token_id,
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
    assert 'network_transaction_id' in response
    assert isinstance(response['network_transaction_id'], str)
    assert len(response['network_transaction_id']) > 0

@pytest.mark.asyncio
async def test_error_expired_card():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': token_id,
            'store_with_provider': False,
            'holder_name': 'CARD_EXPIRED'
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        }
    }

    print(f"Transaction request: {transaction_request}")

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response}")

    # Validate error response structure
    assert isinstance(response, dict)
    assert 'error_codes' in response
    assert isinstance(response['error_codes'], list)
    assert len(response['error_codes']) == 1
    
    # Verify exact error code values
    error = response['error_codes'][0]
    assert error['category'] == ErrorCategory.PAYMENT_METHOD_ERROR
    assert error['code'] == ErrorType.EXPIRED_CARD.code
    
    # Verify provider errors
    assert 'provider_errors' in response
    assert isinstance(response['provider_errors'], list)
    assert len(response['provider_errors']) == 1
    assert response['provider_errors'][0] == 'Expired Card'
    
    # Verify full provider response
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    assert response['full_provider_response']['resultCode'] == 'Refused'
    assert response['full_provider_response']['refusalReason'] == 'Expired Card'
    assert response['full_provider_response']['refusalReasonCode'] == '6'

@pytest.mark.asyncio
async def test_error_invalid_api_key():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk('invalid', 'nope');

    # Create a test transaction request
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token',
            'id': token_id,
            'store_with_provider': False,
            'holder_name': 'CARD_EXPIRED'
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        }
    }

    print(f"Transaction request: {transaction_request}")

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response}")

    # Validate error response structure
    assert isinstance(response, dict)
    assert 'error_codes' in response
    assert isinstance(response['error_codes'], list)
    assert len(response['error_codes']) == 1
    
    # Verify exact error code values
    error = response['error_codes'][0]
    assert error['category'] == ErrorCategory.OTHER
    assert error['code'] == ErrorType.INVALID_API_KEY.code
    
    # Verify provider errors
    assert 'provider_errors' in response
    assert isinstance(response['provider_errors'], list)
    assert len(response['provider_errors']) == 1
    assert response['provider_errors'][0] == 'HTTP Status Response - Unauthorized'
    
    # Verify full provider response
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    assert response['full_provider_response']['status'] == 401
    assert response['full_provider_response']['errorCode'] == '000'
    assert response['full_provider_response']['errorType'] == 'security'
    assert response['full_provider_response']['message'] == 'HTTP Status Response - Unauthorized'

@pytest.mark.asyncio
async def test_token_intents_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token_intent',
            'id': token_intent_id,
            'store_with_provider': False
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        },
        'override_provider_properties': {
            "additionalData": {
                "riskdata.userStatus": "userStatusTest",
                "enhancedSchemeData.customerReference": "customerReferenceTest",
                "autoRescue": "true",
                "enhancedSchemeData.totalTaxAmount": "totalTaxAmountTest"
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
    assert response['source']['type'] in ['basis_theory_token_intent']
    assert 'id' in response['source']
    assert response['source']['provisioned'] == None

    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)

    # Validate networkTransactionId
    assert 'network_transaction_id' in response
    assert isinstance(response['network_transaction_id'], str)
    assert len(response['network_transaction_id']) > 0

@pytest.mark.asyncio
async def test_processor_token_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.UNSCHEDULED,
        'merchant_initiated': True,
        'amount': {
            'value': 1,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'processor_token',
            'id': 'M7HP6FRCWCGZZCV5',
        },
        'customer': {
            'reference': "a57c211b-d6d2-47c6-a7e9-0ca39b2f3acf",
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
    assert response['source']['type'] in ['processor_token']
    assert 'id' in response['source']
    assert response['source']['provisioned'] == None

    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)

    # Validate networkTransactionId
    assert 'network_transaction_id' in response
    assert isinstance(response['network_transaction_id'], str)
    assert len(response['network_transaction_id']) > 0
