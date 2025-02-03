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
    TransactionStatusCode,
    RecurringType,
    RefundRequest,
    RefundResponse,
    ErrorCategory,
    ErrorType,
    Amount,
    Source,
    SourceType,
    Customer,
    TransactionRequest,
    TransactionResponse,
    ThreeDS,
    Address,
    TransactionSource,
    ProvisionedSource
)
from orchestration_sdk.exceptions import TransactionException, ValidationError, BasisTheoryError

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
        'isTest': True,
        'btApiKey': os.getenv('BASISTHEORY_API_KEY'),
        'providerConfig': {
            'adyen': {
                'apiKey': api_key,
                'merchantAccount': merchant_account,
            }
        }
    })

@pytest.mark.asyncio
async def test_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.UNSCHEDULED,
        amount=Amount(value=1, currency='USD'),  # Amount in cents (10.00 in this case)
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
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response.full_provider_response}")

    # Validate response structure
    assert isinstance(response, TransactionResponse)
    assert response.id is not None
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
    assert response.source.provisioned is not None
    assert response.source.provisioned.id is not None
    
    # Validate other fields
    assert response.full_provider_response is not None
    assert isinstance(response.full_provider_response, dict)
    
    assert response.created_at is not None
    # Validate created_at is a valid datetime string
    try:
        # Remove any duplicate timezone offset
        created_at = response.created_at
        if '+00:00+00:00' in created_at:
            created_at = created_at.replace('+00:00+00:00', '+00:00')
        print(f"Created at: {created_at}")
        datetime.fromisoformat(created_at)
    except ValueError:
        pytest.fail("created_at is not a valid ISO datetime string")

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert isinstance(response.network_transaction_id, str)
    assert len(response.network_transaction_id) > 0

@pytest.mark.asyncio
async def test_not_storing_card_on_file():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk(); 

    
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,  # Amount in cents (10.00 in this case)
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
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response.full_provider_response}")

    # Validate response structure
    assert isinstance(response, TransactionResponse)
    assert response.id is not None
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
    assert isinstance(response.full_provider_response, dict)

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert isinstance(response.network_transaction_id, str)
    assert len(response.network_transaction_id) > 0

@pytest.mark.asyncio
async def test_with_three_ds():
    # Create a Basis Theory token
    token_id = await create_bt_token("4917610000000000")

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,  # Amount in cents (10.00 in this case)
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id=token_id,
            store_with_provider=False
        ),
        customer=Customer(
            reference=str(uuid.uuid4())
        ),
        three_ds=ThreeDS(
            eci='05',
            authentication_value='AAABCZIhcQAAAABZlyFxAAAAAAA=',
            xid='AAABCZIhcQAAAABZlyFxAAAAAAA=',
            version='2.2.0'
        )
    )

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response.full_provider_response}")

    # Validate response structure
    assert isinstance(response, TransactionResponse)
    assert response.id is not None
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


    # Validate other fields
    assert response.full_provider_response is not None

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert len(response.network_transaction_id) > 0

@pytest.mark.asyncio
async def test_error_expired_card():
    # Create a Basis Theory token
    token_id = await create_bt_token()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,  # Amount in cents (10.00 in this case)
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
    # Make the transaction request and catch TransactionException
    try:
        response = await sdk.adyen.transaction(transaction_request)
        print(f"Response: {response}")
    except TransactionException as e:
        response = e.error_response
        print(f"Error Response: {response}")

    # Validate error response structure
    assert isinstance(response.error_codes, list)
    assert len(response.error_codes) == 1
    
    # Verify exact error code values
    error = response.error_codes[0]
    assert error.category == ErrorCategory.PAYMENT_METHOD_ERROR
    assert error.code == ErrorType.EXPIRED_CARD.code
    
    # Verify provider errors
    assert isinstance(response.provider_errors, list)
    assert len(response.provider_errors) == 1
    assert response.provider_errors[0] == 'Expired Card'
    
    # Verify full provider response
    assert isinstance(response.full_provider_response, dict)
    assert response.full_provider_response['resultCode'] == 'Refused'
    assert response.full_provider_response['refusalReason'] == 'Expired Card'
    assert response.full_provider_response['refusalReasonCode'] == '6'

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
        amount=Amount(value=1, currency='USD'),  # Amount in cents (10.00 in this case)
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id=token_id,
            store_with_provider=False,
            holder_name='CARD_EXPIRED'
        ),
        customer=Customer(reference=str(uuid.uuid4()))
    )

    print(f"Transaction request: {transaction_request}")
    # Make the transaction request and catch BasisTheoryException
    try:
        response = await sdk.adyen.transaction(transaction_request)
        print(f"Response: {response}")
    except TransactionException as e:
        response = e.error_response
        print(f"BasisTheory Error Response: {response}")

    # Validate error response structure
    assert isinstance(response.error_codes, list)
    assert len(response.error_codes) == 1
    
    # Verify exact error code values
    error = response.error_codes[0]
    assert error.category == ErrorCategory.OTHER
    assert error.code == ErrorType.INVALID_API_KEY.code
    
    # Verify provider errors
    assert len(response.provider_errors) == 1
    assert response.provider_errors[0] == 'HTTP Status Response - Unauthorized'
    
    # Verify full provider response
    assert response.full_provider_response['status'] == 401
    assert response.full_provider_response['errorCode'] == '000'
    assert response.full_provider_response['errorType'] == 'security'
    assert response.full_provider_response['message'] == 'HTTP Status Response - Unauthorized'

@pytest.mark.asyncio
async def test_token_intents_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(value=1, currency='USD'),  # Amount in cents (0.01 in this case)
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN_INTENT,
            id=token_intent_id,
            store_with_provider=False
        ),
        customer=Customer(reference=str(uuid.uuid4()))
    )

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response.full_provider_response}")

    # Validate response structure
    assert response.reference == transaction_request.reference
    
    # Validate amount
    assert response.amount.value == transaction_request.amount.value
    assert response.amount.currency == transaction_request.amount.currency
    
    # Validate status
    assert response.status.code == TransactionStatusCode.AUTHORIZED
    assert response.status.provider_code == 'Authorised'
    
    # Validate source
    assert response.source.type == SourceType.BASIS_THEORY_TOKEN_INTENT
    assert response.source.id == token_intent_id
    assert response.source.provisioned is None

    # Validate other fields
    assert response.full_provider_response is not None
    assert isinstance(response.full_provider_response, dict)

    # Validate network_transaction_id
    assert response.network_transaction_id is not None
    assert isinstance(response.network_transaction_id, str)
    assert len(response.network_transaction_id) > 0

@pytest.mark.asyncio
async def test_processor_token_charge_not_storing_card_on_file(): 
    # Create a Basis Theory token
    token_intent_id = await create_bt_token_intent()

    # Initialize the SDK with environment variables
    sdk = get_sdk();

    
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.UNSCHEDULED,
        merchant_initiated=True,
        amount=Amount(value=1, currency='USD'),  # Amount in cents (0.01 in this case)
        source=Source(
            type=SourceType.PROCESSOR_TOKEN,
            id='M7HP6FRCWCGZZCV5'
        ),
        customer=Customer(
            reference="a57c211b-d6d2-47c6-a7e9-0ca39b2f3acf"
        )
    )

    # Make the transaction request
    response = await sdk.adyen.transaction(transaction_request)
    print(f"Response: {response.full_provider_response}")

    # Validate response structure
    assert response.reference == transaction_request.reference
    
    # Validate amount
    assert response.amount.value == transaction_request.amount.value
    assert response.amount.currency == transaction_request.amount.currency
    
    # Validate status
    assert response.status.code == TransactionStatusCode.AUTHORIZED
    assert response.status.provider_code == 'Authorised'
    
    # Validate source
    assert response.source.type == SourceType.PROCESSOR_TOKEN
    assert response.source.id == transaction_request.source.id
    assert response.source.provisioned is None
    # Validate other fields
    assert response.full_provider_response is not None
    assert isinstance(response.full_provider_response, dict)

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
    response = await sdk.adyen.transaction(transaction_request)
    
    refund_request = RefundRequest(
        original_transaction_id=response.id,
        reference=f"{transaction_request.reference}_refund",
        amount=Amount(value=500, currency='USD')
    )

    # Process the refund
    refund_response = await sdk.adyen.refund_transaction(refund_request)

    # Verify refund succeeded
    assert refund_response.reference == refund_request.reference
    assert refund_response.id != refund_request.original_transaction_id
    assert refund_response.refunded_transaction_id == refund_request.original_transaction_id
    assert refund_response.amount.value == refund_request.amount.value
    assert refund_response.amount.currency == refund_request.amount.currency
    assert refund_response.status.code == TransactionStatusCode.RECEIVED
    assert refund_response.status.provider_code == "received"