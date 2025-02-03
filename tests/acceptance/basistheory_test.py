# test_sdk.py
import os
import uuid
import pytest
from datetime import datetime
from dotenv import load_dotenv
from orchestration_sdk import PaymentOrchestrationSDK
from orchestration_sdk.models import (
    TransactionResponse,
    TransactionStatus,
    TransactionSource,
    TransactionStatusCode,
    RecurringType,
    ErrorCategory,
    ErrorType,
    TransactionRequest,
    Amount,
    Source,
    Customer,
    SourceType
)
from orchestration_sdk.exceptions import BasisTheoryError

# Load environment variables from .env file
load_dotenv()

@pytest.mark.asyncio
async def test_error_invalid_api_key():
    # Initialize the SDK with environment variables
    sdk = PaymentOrchestrationSDK.init({
        'is_test': True,
        'bt_api_key': "invalid",
        'provider_config': {
            'adyen': {
                'api_key': "invalid",
                'merchant_account': "nope",
            }
        }
    })

    # Create a test transaction request
    transaction_request = TransactionRequest(
        reference=str(uuid.uuid4()),  # Unique reference for the transaction
        type=RecurringType.ONE_TIME,
        amount=Amount(
            value=1,  # Amount in cents (10.00 in this case)
            currency='USD'
        ),
        source=Source(
            type=SourceType.BASIS_THEORY_TOKEN,
            id='46f2f39e-6c33-457c-a64e-292c55c2ddc9',  # Replace with a real stored payment method ID
            store_with_provider=False,
            holder_name='CARD_EXPIRED'
        ),
        customer=Customer(
            reference=str(uuid.uuid4()),
        )
    )


    print(f"Transaction request: {transaction_request}")

    # Make the transaction request and expect a BasisTheoryError
    with pytest.raises(BasisTheoryError) as exc_info:
        await sdk.adyen.transaction(transaction_request)

    error = exc_info.value
    
    # Verify error details
    assert error.status == 401
    assert len(error.error_response.error_codes) == 1
    assert error.error_response.error_codes[0].code == ErrorType.BT_UNAUTHENTICATED.code
    assert error.error_response.provider_errors == []
    assert error.error_response.full_provider_response['proxy_error']['detail'] == 'The BT-API-KEY header is required'