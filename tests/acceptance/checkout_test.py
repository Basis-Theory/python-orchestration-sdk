# test_sdk.py
import os
import json
import uuid
import asyncio
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


async def create_bt_token(card_number: str = "4242424242424242", expiration_year: str = "2030", expiration_month: str = "03", cvc: str = "100"):
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
                "expiration_month": expiration_month,
                "expiration_year": expiration_year,
                "cvc": cvc
            },
            "expires_at": expires_at
        })
        return token.id

async def create_bt_token_intent(card_number: str = "4242424242424242", cvc: str = "737"):
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
            "cvc": cvc
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    print(f"Response: {response_data}")
    return response_data['id']

def get_sdk(processing_channel = os.getenv('CHECKOUT_PROCESSING_CHANNEL'), private_key = os.getenv('CHECKOUT_PRIVATE_KEY')):
    return PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': os.getenv('BASISTHEORY_API_KEY'),
        'providerConfig': {
            'checkout': {
                'private_key': private_key,
                'processing_channel': processing_channel
            }
        }
    })  

@pytest.mark.asyncio
async def test_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk()

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
    print(f"Response: {response}")

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

    # Validate networkTransactionId
    assert 'networkTransactionId' in response
    assert isinstance(response['networkTransactionId'], str)
    assert len(response['networkTransactionId']) > 0
    
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


@pytest.mark.asyncio
async def test_not_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk()

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
            'id': token_id,
            'store_with_provider': False
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        }
    }

    # Make the transaction request
    response = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {json.dumps(response['full_provider_response'], indent=2)}")

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
    # Create a Basis Theory token
    token_id = await create_bt_token("4242424242424242")

    # Initialize the SDK with environment variables
    sdk = get_sdk();

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
            'id': token_id,
            'store_with_provider': False
        },
        'customer': {
            'reference': str(uuid.uuid4()),
            'address': {
                'address_line1': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'zip': '10001',
                'country': 'CA'
            }
        },
        'three_ds': {
            'eci': '05',
            'authentication_value': 'AAABCZIhcQAAAABZlyFxAAAAAAA=',
            'xid': 'AAABCZIhcQAAAABZlyFxAAAAAAA=',
            'version': '2.2.0'
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
    assert response['source']['provisioned'] == None

    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)

    # Validate networkTransactionId
    assert 'networkTransactionId' in response
    assert isinstance(response['networkTransactionId'], str)
    assert len(response['networkTransactionId']) > 0

@pytest.mark.asyncio
async def test_error_expired_card():
    # Create a Basis Theory token
    token_id = await create_bt_token("4724117215951699", "2024", "03", "100")

    # Initialize the SDK with environment variables
    sdk = get_sdk();

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
            'id': token_id,
            'store_with_provider': False,
        },
        'customer': {
            'reference': str(uuid.uuid4()),
            'address': {
                'address_line1': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'zip': '10001',
                'country': 'GB'
            }
        }
    }

    print(f"Transaction request: {transaction_request}")

    # Make the transaction request
    response = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {json.dumps(response['full_provider_response'], indent=2)}")

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
    assert response['provider_errors'] == ['card_expired']
    
    # Verify full provider response
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    assert response['full_provider_response']['error_type'] == 'processing_error'
    assert response['full_provider_response']['error_codes'] == ['card_expired']

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
            'holderName': 'CARD_EXPIRED'
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        }
    }

    print(f"Transaction request: {transaction_request}")

    # Make the transaction request
    response = await sdk.checkout.transaction(transaction_request)
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
    assert len(response['provider_errors']) == 0

    
    # Verify full provider response
    assert 'full_provider_response' in response

@pytest.mark.asyncio
async def test_token_intents_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create a test transaction with a processor token
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
    assert response['source']['type'] in ['basis_theory_token_intent']
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
async def test_processor_token_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    token_id = 'src_ije5kt7nbntexlkijjuw4ezmfm'

    # Create a test transaction with a processor token
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
            'id': token_id,
        },
        'customer': {
            'reference': "a57c211b-d6d2-47c6-a7e9-0ca39b2f3acf",
        }
    }

    # Make the transaction request
    response = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {response}")

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
    assert response['source']['provisioned'] == { 'id': token_id }
    # Validate other fields
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)

    # Validate networkTransactionId
    assert 'networkTransactionId' in response
    assert isinstance(response['networkTransactionId'], str)
    assert len(response['networkTransactionId']) > 0


@pytest.mark.asyncio
async def test_partial_refund():
   # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create a test transaction with a processor token
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 1000,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token_intent',
            'id': token_intent_id,
            'store_with_provider': False
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        }
    }

    # Make the transaction request
    response = await sdk.checkout.transaction(transaction_request)
    
    refund_request = {
        'reference': f"{transaction_request.get('reference')}_refund",
        'amount': 500
    }

    # Process the refund
    refund_response = await sdk.checkout.refund_transaction(response['id'], refund_request)

    # Verify refund succeeded
    assert refund_response.get('reference') == refund_request.get('reference')
    assert refund_response.get('status').get('code') == TransactionStatusCode.REFUNDED

@pytest.mark.asyncio
async def test_failed_refund():
   # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create a test transaction with a processor token
    transaction_request = {
        'reference': str(uuid.uuid4()),  # Unique reference for the transaction
        'type': RecurringType.ONE_TIME,
        'amount': {
            'value': 3738,  # Amount in cents (10.00 in this case)
            'currency': 'USD'
        },
        'source': {
            'type': 'basis_theory_token_intent',
            'id': token_intent_id,
            'store_with_provider': False
        },
        'customer': {
            'reference': str(uuid.uuid4()),
        }
    }

    # Make the transaction request
    response = await sdk.checkout.transaction(transaction_request)
    
    refund_request = {
        'reference': f"{transaction_request.get('reference')}_refund",
        'amount': 3738
    }
    
    # Process the refund
    refund_response = await sdk.checkout.refund_transaction(response['id'], refund_request)

    # Verify refund failed with correct error
    assert refund_response.get('error_codes')[0].get('category') == ErrorCategory.PROCESSING_ERROR
    assert refund_response.get('error_codes')[0].get('code') == 'refund_declined'


@pytest.mark.asyncio
async def test_failed_refund_amount_exceeds_balance():
   # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create a test transaction with a processor token
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
        }
    }

    # Make the transaction request
    response = await sdk.checkout.transaction(transaction_request)
    
    refund_request = {
        'reference': f"{transaction_request.get('reference')}_refund",
        'amount': 200
    }
    
    # Process the refund
    refund_response = await sdk.checkout.refund_transaction(response['id'], refund_request)

    # Verify refund failed with correct error
    assert refund_response.get('error_codes')[0].get('category') == ErrorCategory.PROCESSING_ERROR
    assert refund_response.get('error_codes')[0].get('code') == 'refund_amount_exceeds_balance'


async def run_transactions_for_list(channel, transactions):
    sdk = get_sdk(channel)

   # Process each transaction
    for tx_data in transactions:
        print(f"Processing transaction: {tx_data['card_number']}")
        # Create a Basis Theory token for each card number
        token_id = await create_bt_token_intent(tx_data['card_number'], tx_data['cvc'])

        # Convert amount to cents (multiply by 100 and round)
        amount_cents = round(tx_data['amount'] * 100)

        # Create a test transaction request
        transaction_request = {
            'reference': tx_data['reference'],
            'type': RecurringType.ONE_TIME,
            'amount': {
                'value': amount_cents,
                'currency': tx_data['currency']
            },
            'source': {
                'type': 'basis_theory_token_intent',
                'id': token_id,
                'store_with_provider': False,
                'holderName': f"{tx_data['first_name']} {tx_data['last_name']}"
            },
            'customer': {
                'reference': str(uuid.uuid4()),
                'first_name': tx_data['first_name'],
                'last_name': tx_data['last_name'],
                'email': tx_data['email'],
                'address': {
                    'address_line1': tx_data['address'],
                    'address_line2': tx_data['address2'] if tx_data['address2'] else None,
                    'city': tx_data['city'],
                    'state': tx_data['state'],
                    'zip': tx_data['zip'],
                    'country': tx_data['country']
                }
            }
        }

        # Make the transaction request
        response = await sdk.checkout.transaction(transaction_request)
        print(f"Response for reference {tx_data['reference']}: {response}")

        # Validate response structure
        assert isinstance(response, dict)
        assert 'reference' in response
        assert response['reference'] == transaction_request['reference']

        if 'refund' in tx_data:
            refund_request = {
                'reference': tx_data['refund']['reference'],
                'amount': round(tx_data['refund']['amount'] * 100)
            }
            
            refund_response = await sdk.checkout.refund_transaction(response['id'], refund_request)   
            print(f"Refund response for reference {tx_data['reference']}: {refund_response}")

            assert 'reference' in refund_response
            assert refund_response['reference'] == refund_request['reference']


# @pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping test_run_checkout_verification")
async def test_run_checkout_verification():
    # Test data for multiple transactions
    from faker import Faker

    # Initialize Faker
    fake = Faker()

    us_processing_channel = os.getenv('CHECKOUT_PROCESSING_CHANNEL')
    eu_processing_channel = os.getenv('CHECKOUT_PROCESSING_CHANNEL_EU')

    eu_transactions = [
        {
            'reference': '962080081111', 'currency': 'USD', 'amount': 1.992,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US', 'refund': {
                'reference': '962080081222',
                'amount': 1.992
            }
        },
        {
            'reference': '962080080772', 'currency': 'EUR', 'amount': 234.835,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US'
        },
        {
            'reference': '962080081382', 'currency': 'EUR', 'amount': 2.863,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': fake.country_code()
        },
        {
            'reference': '962080081098', 'currency': 'GBP', 'amount': 1.966,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': fake.country_code()
        },
        {
            'reference': '962080081711', 'currency': 'EUR', 'amount': 2.873,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': fake.country_code()
        },
        {
            'reference': '962080081376', 'currency': 'GBP', 'amount': 112.556,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': fake.country_code(), 'refund': {
                'reference': '962080081396',
                'amount': 112.556
            }
        },
        {
            'reference': '962080081152', 'currency': 'EUR', 'amount': 1.964,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': fake.country_code()
        },
        {
            'reference': '962080081901', 'currency': 'USD', 'amount': 25.803,
            'card_number': '5436031030606378', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': fake.country_code()
        },
        {
            'reference': '962080081979', 'currency': 'USD', 'amount': 4.772,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': fake.country_code()
        }
    ]

    us_transactions = [
        {
            'reference': '962080080425', 'currency': 'USD', 'amount': 1600,
            'card_number': '5436031030606378', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US'
        },
        {
            'reference': '962080080343', 'currency': 'USD', 'amount': 100,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US'
        },
        {
            'reference': '962080081048', 'currency': 'USD', 'amount': 9.836,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US'
        },
        {
            'reference': '962080080707', 'currency': 'USD', 'amount': 1.26,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'DE'
        },
        {
            'reference': '962080081000', 'currency': 'USD', 'amount': 1.25,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US'
        },
        {
            'reference': '962080080858', 'currency': 'CAD', 'amount': 90,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'CA'
        },
        {
            'reference': '962080081732', 'currency': 'CAD', 'amount': 9.32,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'CA'
        },
        {
            'reference': '962080081159', 'currency': 'USD', 'amount': 942.16,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'CA'
        },
        {
            'reference': '962080081267', 'currency': 'USD', 'amount': 9.712,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'CA', 'refund': {
                'reference': '962080081267',
                'amount': 9.712
            }
        },
        {
            'reference': '962080081518', 'currency': 'CAD', 'amount': 51.424,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'CA', 'refund': {
                'reference': '962080081518',
                'amount': 51.424,
            }
        },
        {
            'reference': '962080081288', 'currency': 'CAD', 'amount': 2103.009,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': fake.secondary_address(),
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'CA'
        },
        {
            'reference': '962080082090', 'currency': 'USD', 'amount': 18.93327,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'HK'
        },
        {
            'reference': '962080082082', 'currency': 'USD', 'amount': 5.034966,
            'card_number': '6011111111111117', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US'
        },
        {
            'reference': '962080081874', 'currency': 'CAD', 'amount': 152.7545,
            'card_number': '4242424242424242', 'cvc': '737', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': fake.secondary_address(),
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'US'
        },
        {
            'reference': '962080081473', 'currency': 'USD', 'amount': 1003.405,
            'card_number': '345678901234564', 'cvc': '7371', 'first_name': fake.first_name(), 'last_name': fake.last_name(),
            'email': fake.email(), 'address': fake.street_address(), 'address2': '',
            'city': fake.city(), 'state': fake.state(), 'zip': fake.postcode(), 'country': 'CA', 'refund': {
                'reference': '972080081475',
                'amount': 1003.405
            }
        }
    ]

    # Initialize the SDK with environment variables
    await run_transactions_for_list(us_processing_channel, us_transactions)
    await run_transactions_for_list(eu_processing_channel, eu_transactions)


    