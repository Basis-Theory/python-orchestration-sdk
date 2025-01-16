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
    ErrorType
)

# Load environment variables from .env file
load_dotenv()

@pytest.mark.asyncio
async def test_error_invalid_api_key():
    # Initialize the SDK with environment variables
    sdk = PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': "invalid",
        'providerConfig': {
            'adyen': {
                'apiKey': "invalid",
                'merchantAccount': "nope",
            }
        }
    })

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
            'id': '46f2f39e-6c33-457c-a64e-292c55c2ddc9',  # Replace with a real stored payment method ID
            'store_with_provider': False,
            'holderName': 'CARD_EXPIRED'
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
    assert error['category'] == ErrorCategory.BASIS_THEORY_ERROR
    assert error['code'] == ErrorType.BT_UNAUTHENTICATED.code
    
    # Verify provider errors
    assert 'provider_errors' in response
    assert isinstance(response['provider_errors'], list)
    assert len(response['provider_errors']) == 0    
    
    # Verify full provider response
    assert 'full_provider_response' in response
    assert isinstance(response['full_provider_response'], dict)
    assert response['full_provider_response']['proxy_error']['status'] == 401
    assert response['full_provider_response']['proxy_error']['errors'] == {}
    assert response['full_provider_response']['proxy_error']['detail'] == 'The BT-API-KEY header is required'
    assert response['full_provider_response']['proxy_error']['title'] == 'Unauthorized proxy request'