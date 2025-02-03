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
    RefundResponse,
    RefundRequest,
    ErrorCategory,
    ErrorType,
    Amount,
    Source,
    SourceType,
    Customer,
    Address,
    ThreeDS,
    TransactionRequest,
    TransactionResponse,
    TransactionStatusCode,
    RecurringType,
    RefundRequest,
    RefundResponse,
    ErrorCategory,
    ErrorType
)
from orchestration_sdk.exceptions import TransactionException, ValidationError

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
        'is_test': True,
        'bt_api_key': os.getenv('BASISTHEORY_API_KEY'),
        'provider_config': {
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

    # Create transaction request
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),
        type=RecurringType.UNSCHEDULED,
        amount=Amount(
            value=100,
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id=token_id,
            store_with_provider=True,
            holder_name='John Doe'
        ),
        customer=Customer(
            reference=str(uuid.uuid4()),
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            address=Address(
                address_line1='123 Main St',
                city='New York',
                state='NY',
                zip='10001',
                country='US'
            )
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {response}")

    # Validate response structure
    assert response.id is not None
    assert response.reference is not None
    assert response.reference == transaction_request.reference
    
    # Validate amount
    assert response.amount is not None
    assert response.amount.value is not None
    assert response.amount.currency == 'USD'
    
    # Validate status
    assert response.status is not None
    assert response.status.code == TransactionStatusCode.AUTHORIZED
    assert response.status.provider_code is not None
    
    # Validate source
    assert response.source is not None
    assert response.source.type in [SourceType.BASIS_THEORY_TOKEN]
    assert response.source.id is not None
    assert response.source.provisioned is not None
    assert response.source.provisioned.id is not None

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert len(response.network_transaction_id) > 0

    # Validate other fields
    assert response.full_provider_response is not None
    
    assert response.created_at is not None
    # Optionally validate created_at is a valid datetime string
    try:
        datetime.fromisoformat(response.created_at.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("created_at is not a valid ISO datetime string")


@pytest.mark.asyncio
async def test_not_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk()

    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id=token_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4())
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {json.dumps(response.full_provider_response, indent=2)}")

    # Validate response structure
    assert response.id is not None
    assert response.reference is not None
    assert response.reference == transaction_request.reference
    
    # Validate amount
    assert response.amount is not None
    assert response.amount.value is not None
    assert response.amount.currency == 'USD'
    
    # Validate status
    assert response.status is not None
    assert response.status.code == TransactionStatusCode.AUTHORIZED
    assert response.status.provider_code is not None
    
    # Validate source
    assert response.source is not None
    assert response.source.type == SourceType.BASIS_THEORY_TOKEN
    assert response.source.id is not None
    assert response.source.provisioned is None

    # Validate other fields
    assert response.full_provider_response is not None

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert len(response.network_transaction_id) > 0

@pytest.mark.asyncio
async def test_with_three_ds():
    # Create a Basis Theory token
    token_id = await create_bt_token("4242424242424242")

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create transaction request
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id=token_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4()),
            address=Address(
                address_line1='123 Main St',
                city='New York', 
                state='NY',
                zip='10001',
                country='CA'
            )
        ),
        three_ds=ThreeDS(
            eci='05',
            authentication_value='AAABCZIhcQAAAABZlyFxAAAAAAA=',
            xid='AAABCZIhcQAAAABZlyFxAAAAAAA=',
            version='2.2.0'
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {json.dumps(response.full_provider_response, indent=2)}")

    # Validate response structure
    assert response.id is not None
    assert response.reference is not None
    assert response.reference == transaction_request.reference
    
    # Validate amount
    assert response.amount is not None
    assert response.amount.value is not None
    assert response.amount.currency == 'USD'
    
    # Validate status
    assert response.status is not None
    assert response.status.code == TransactionStatusCode.AUTHORIZED
    assert response.status.provider_code is not None
    
    # Validate source
    assert response.source is not None
    assert response.source.type == SourceType.BASIS_THEORY_TOKEN
    assert response.source.id is not None
    assert response.source.provisioned is None

    # Validate other fields
    assert response.full_provider_response is not None

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert isinstance(response.network_transaction_id, str)
    assert len(response.network_transaction_id) > 0

@pytest.mark.asyncio
async def test_error_expired_card():
    # Create a Basis Theory token
    token_id = await create_bt_token("4724117215951699", "2024", "03", "100")

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,  # Amount in cents
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id=token_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4()),
            address=Address(
                address_line1='123 Main St',
                city='New York', 
                state='NY',
                zip='10001',
                country='GB'
            )
        )
    )

    print(f"Transaction request: {transaction_request}")

    # Make the transaction request and expect a TransactionException
    with pytest.raises(TransactionException) as exc_info:
        await sdk.checkout.transaction(transaction_request)

    # Get the error response from the exception
    error_response = exc_info.value.error_response
    print(f"Error Response: {json.dumps(error_response.full_provider_response, indent=2)}")

    # Validate error response structure
    assert len(error_response.error_codes) == 1
    
    # Verify exact error code values
    error = error_response.error_codes[0]
    assert error.category == ErrorCategory.PAYMENT_METHOD_ERROR
    assert error.code == ErrorType.EXPIRED_CARD.code
    
    # Verify provider errors
    assert isinstance(error_response.provider_errors, list)
    assert len(error_response.provider_errors) == 1
    assert error_response.provider_errors == ['card_expired']
    
    # Verify full provider response
    assert isinstance(error_response.full_provider_response, dict)
    assert error_response.full_provider_response['error_type'] == 'processing_error'
    assert error_response.full_provider_response['error_codes'] == ['card_expired']

@pytest.mark.asyncio
async def test_error_invalid_api_key():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk('invalid', 'nope');

    # Create a test transaction request
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,  # Amount in cents
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id=token_id,
            store_with_provider=False,
            holder_name='CARD_EXPIRED'
        ),
        customer=Customer(
            reference=str(uuid.uuid4())
        )
    )

    print(f"Transaction request: {transaction_request}")

    # Make the transaction request and expect a TransactionException
    with pytest.raises(TransactionException) as exc_info:
        await sdk.checkout.transaction(transaction_request)

    # Get the error response from the exception
    error_response = exc_info.value.error_response
    print(f"Error Response: {error_response}")

    # Validate error response structure
    assert len(error_response.error_codes) == 1
    
    # Verify exact error code values
    error = error_response.error_codes[0]
    assert error.category == ErrorCategory.OTHER
    assert error.code == ErrorType.INVALID_API_KEY.code
    
    # Verify provider errors
    assert isinstance(error_response.provider_errors, list)
    assert len(error_response.provider_errors) == 0
    
    # Verify full provider response
    assert error_response.full_provider_response is None

@pytest.mark.asyncio
async def test_token_intents_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create transaction request
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN_INTENT,
            id=token_intent_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4())
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {response.full_provider_response}")

    # Validate response structure
    assert response.id is not None
    assert response.reference is not None
    assert response.reference == transaction_request.reference
    
    # Validate amount
    assert response.amount is not None
    assert response.amount.value is not None
    assert response.amount.currency == 'USD'
    
    # Validate status
    assert response.status is not None
    assert response.status.code == TransactionStatusCode.AUTHORIZED
    assert response.status.provider_code is not None
    
    # Validate source
    assert response.source is not None
    assert response.source.type == SourceType.BASIS_THEORY_TOKEN_INTENT
    assert response.source.id is not None
    assert response.source.provisioned is None

    # Validate other fields
    assert response.full_provider_response is not None

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert len(response.network_transaction_id) > 0

@pytest.mark.asyncio
async def test_processor_token_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create initial transaction to get processor token
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.UNSCHEDULED,
        amount=Amount(value=100, currency='USD'),  # Amount in cents
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN_INTENT,
            id=token_intent_id,
            store_with_provider=True,
            holder_name='John Doe'
        ),
        customer=Customer(
            reference=str(uuid.uuid4()),
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            address=Address(
                address_line1='123 Main St',
                city='New York',
                state='NY',
                zip='10001',
                country='US'
            )
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)

    token_id = response.source.provisioned.id

    # Create a test transaction with a processor token
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.UNSCHEDULED,
        merchant_initiated=True,
        amount=Amount(value=1, currency='USD'),  # Amount in cents
        source=Source(
            type=SourceType.PROCESSOR_TOKEN,
            id=token_id,
        ),
        customer=Customer(
            reference="a57c211b-d6d2-47c6-a7e9-0ca39b2f3acf",
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    print(f"Response: {response}")

    # Validate response structure
    assert response.id is not None
    assert response.reference is not None
    assert response.reference == transaction_request.reference
    
    # Validate amount
    assert response.amount is not None
    assert response.amount.value is not None
    assert response.amount.currency == 'USD'
    
    # Validate status
    assert response.status is not None
    assert response.status.code == TransactionStatusCode.AUTHORIZED
    assert response.status.provider_code is not None
    
    # Validate source
    assert response.source is not None
    assert response.source.type == SourceType.PROCESSOR_TOKEN
    assert response.source.id is not None
    assert response.source.provisioned is not None
    assert response.source.provisioned.id == token_id

    # Validate other fields
    assert response.full_provider_response is not None

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert isinstance(response.network_transaction_id, str)
    assert len(response.network_transaction_id) > 0


@pytest.mark.asyncio
async def test_partial_refund():
   # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create a test transaction with a processor token
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1000,  # Amount in cents (10.00 in this case)
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN_INTENT,
            id=token_intent_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4())
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    
    refund_request = RefundRequest(
        original_transaction_id=response.id,
        reference=f"{transaction_request.reference}_refund",
        amount=Amount(value=500, currency='USD')
    )

    # Process the refund
    refund_response = await sdk.checkout.refund_transaction(refund_request)

    # Verify refund succeeded
    assert refund_response.reference == refund_request.reference
    assert refund_response.status.code == TransactionStatusCode.RECEIVED

@pytest.mark.asyncio
async def test_failed_refund():
   # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create a test transaction with a processor token
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=3738,  # Amount in cents
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN_INTENT,
            id=token_intent_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4())
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    
    refund_request = RefundRequest(
        original_transaction_id=response.id,
        reference=f"{transaction_request.reference}_refund",
        amount=Amount(value=3738, currency='USD')
    )
    # Process the refund and expect a TransactionException
    with pytest.raises(TransactionException) as exc_info:
        await sdk.checkout.refund_transaction(refund_request)

    # Get the error response from the exception
    error_response = exc_info.value.error_response

    # Verify refund failed with correct error
    assert error_response.error_codes[0].category == ErrorCategory.PROCESSING_ERROR
    assert error_response.error_codes[0].code == 'refund_declined'


@pytest.mark.asyncio
async def test_failed_refund_amount_exceeds_balance():
   # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    # Create a test transaction with a processor token
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,  # Amount in cents (10.00 in this case)
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN_INTENT,
            id=token_intent_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4())
        )
    )

    # Make the transaction request
    response: TransactionResponse = await sdk.checkout.transaction(transaction_request)
    
    refund_request = RefundRequest(
        original_transaction_id=response.id,
        reference=f"{transaction_request.reference}_refund",
        amount=Amount(value=200, currency='USD')
    )
    # Process the refund and expect a TransactionException
    with pytest.raises(TransactionException) as exc_info:
        await sdk.checkout.refund_transaction(refund_request)

    # Get the error response from the exception
    error_response = exc_info.value.error_response

    # Verify refund failed with correct error
    assert error_response.error_codes[0].category == ErrorCategory.PROCESSING_ERROR
    assert error_response.error_codes[0].code == 'refund_amount_exceeds_balance'


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
                'holder_name': f"{tx_data['first_name']} {tx_data['last_name']}"
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

