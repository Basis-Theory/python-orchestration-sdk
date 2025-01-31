import os
import uuid
import pytest
import requests
from datetime import datetime
from unittest.mock import MagicMock, patch
from orchestration_sdk import PaymentOrchestrationSDK
from orchestration_sdk.models import (
    TransactionStatusCode,
    RecurringType,
    SourceType,
    ErrorCategory,
    ErrorType,
    TransactionException
)

@pytest.mark.asyncio
async def test_errors():
    # Define test cases mapping
    test_cases = [
        {"error_type": "processing_error", "error_codes": ["card_authorization_failed"], "expected_error": ErrorType.REFUSED},
        {"error_type": "processing_error", "error_codes": ["card_disabled"], "expected_error": ErrorType.BLOCKED_CARD},
        {"error_type": "processing_error", "error_codes": ["card_expired"], "expected_error": ErrorType.EXPIRED_CARD},
        {"error_type": "processing_error", "error_codes": ["card_expiry_month_invalid"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["card_expiry_month_required"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["card_expiry_year_invalid"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["card_expiry_year_required"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["expiry_date_format_invalid"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["card_not_found"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["card_number_invalid"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["card_number_required"], "expected_error": ErrorType.INVALID_CARD},
        {"error_type": "processing_error", "error_codes": ["issuer_network_unavailable"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["card_not_eligible_domestic_money_transfer"], "expected_error": ErrorType.NOT_SUPPORTED},
        {"error_type": "processing_error", "error_codes": ["card_not_eligible_cross_border_money_transfer"], "expected_error": ErrorType.NOT_SUPPORTED},
        {"error_type": "processing_error", "error_codes": ["card_not_eligible_domestic_non_money_transfer"], "expected_error": ErrorType.NOT_SUPPORTED},
        {"error_type": "processing_error", "error_codes": ["card_not_eligible_cross_border_non_money_transfer"], "expected_error": ErrorType.NOT_SUPPORTED},
        {"error_type": "processing_error", "error_codes": ["card_not_eligible_domestic_online_gambling"], "expected_error": ErrorType.NOT_SUPPORTED},
        {"error_type": "processing_error", "error_codes": ["card_not_eligible_cross_border_online_gambling"], "expected_error": ErrorType.NOT_SUPPORTED},
        {"error_type": "processing_error", "error_codes": ["3ds_not_enabled_for_card"], "expected_error": ErrorType.AUTHENTICATION_FAILURE},
        {"error_type": "processing_error", "error_codes": ["3ds_not_supported"], "expected_error": ErrorType.AUTHENTICATION_FAILURE},
        {"error_type": "processing_error", "error_codes": ["amount_exceeds_balance"], "expected_error": ErrorType.INSUFFICENT_FUNDS},
        {"error_type": "processing_error", "error_codes": ["amount_limit_exceeded"], "expected_error": ErrorType.INSUFFICENT_FUNDS},
        {"error_type": "processing_error", "error_codes": ["payment_expired"], "expected_error": ErrorType.PAYMENT_CANCELLED},
        {"error_type": "processing_error", "error_codes": ["cvv_invalid"], "expected_error": ErrorType.CVC_INVALID},
        {"error_type": "processing_error", "error_codes": ["processing_error"], "expected_error": ErrorType.REFUSED},
        {"error_type": "processing_error", "error_codes": ["velocity_amount_limit_exceeded"], "expected_error": ErrorType.INSUFFICENT_FUNDS},
        {"error_type": "processing_error", "error_codes": ["velocity_count_limit_exceeded"], "expected_error": ErrorType.INSUFFICENT_FUNDS},
        {"error_type": "processing_error", "error_codes": ["address_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["city_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["country_address_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["country_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["country_phone_code_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["country_phone_code_length_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["phone_number_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["phone_number_length_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["zip_invalid"], "expected_error": ErrorType.AVS_DECLINE},
        {"error_type": "processing_error", "error_codes": ["action_failure_limit_exceeded"], "expected_error": ErrorType.PROCESSOR_BLOCKED},
        {"error_type": "processing_error", "error_codes": ["token_expired"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["token_in_use"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["token_invalid"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["token_used"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["capture_value_greater_than_authorized"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["capture_value_greater_than_remaining_authorized"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["card_holder_invalid"], "expected_error": ErrorType.OTHER},
        {"error_type": "processing_error", "error_codes": ["previous_payment_id_invalid"], "expected_error": ErrorType.OTHER}
    ]

    # Initialize the SDK
    sdk = PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': 'test_bt_api_key',
        'providerConfig': {
            'checkout': {
                'private_key': 'test_private_key',
                'processing_channel': 'test_channel',
            }
        }
    })

    for test_case in test_cases:
        # Create mock response data
        mock_response_data = {
            "request_id": "8837544667111111",
            "error_type": test_case["error_type"],
            "error_codes": test_case["error_codes"]
        }

        # Create a mock response that raises HTTPError
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 422
        mock_response.ok = False

        # Create a mock HTTPError
        mock_error = requests.exceptions.HTTPError(response=mock_response)
        mock_error.response = mock_response

        # Create a test transaction request
        transaction_request = {
            'reference': str(uuid.uuid4()),
            'type': RecurringType.ONE_TIME,
            'amount': {
                'value': 1,
                'currency': 'USD'
            },
            'source': {
                'type': SourceType.PROCESSOR_TOKEN,
                'id': 'test_token_id',
                'store_with_provider': False
            },
            'customer': {
                'reference': str(uuid.uuid4())
            }
        }

        # Mock the session.request method to raise HTTPError
        with patch('requests.request', side_effect=mock_error) as mock_request:
            # Make the transaction request and expect a TransactionException
            with pytest.raises(TransactionException) as exc_info:
                await sdk.checkout.transaction(transaction_request)

            # Get the error response from the exception
            error_response = exc_info.value.error_response

            # Verify the request was made with correct parameters
            mock_request.assert_called_once()

            # Validate error response structure
            assert isinstance(error_response.error_codes, list)
            assert len(error_response.error_codes) == 1

            # Verify exact error code values
            error = error_response.error_codes[0]
            assert error.code == test_case["expected_error"].code

            # Verify provider errors
            assert isinstance(error_response.provider_errors, list)
            assert len(error_response.provider_errors) == len(test_case["error_codes"])
            assert error_response.provider_errors == test_case["error_codes"]

            # Verify full provider response
            assert isinstance(error_response.full_provider_response, dict)
            assert error_response.full_provider_response['error_type'] == test_case["error_type"]
            assert error_response.full_provider_response['error_codes'] == test_case["error_codes"]
