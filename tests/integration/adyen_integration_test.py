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
    ErrorType,
    TransactionRequest,
    Amount,
    Source,
    Customer,
    Address
)
from orchestration_sdk.exceptions import TransactionError

@pytest.mark.asyncio
async def test_errors():
    # Define test cases mapping
    test_cases = [
        {"holder_name": "UNKNOWN", "resultCode": "Error", "refusalReason": "Unknown", "refusalReasonCode": "0", "expected_error": ErrorType.OTHER},
        {"holder_name": "DECLINED", "resultCode": "Refused", "refusalReason": "Refused", "refusalReasonCode": "2", "expected_error": ErrorType.REFUSED},
        {"holder_name": "REFERRAL", "resultCode": "Refused", "refusalReason": "Referral", "refusalReasonCode": "3", "expected_error": ErrorType.REFERRAL},
        {"holder_name": "ERROR", "resultCode": "Error", "refusalReason": "Acquirer Error", "refusalReasonCode": "4", "expected_error": ErrorType.ACQUIRER_ERROR},
        {"holder_name": "BLOCK_CARD", "resultCode": "Refused", "refusalReason": "Blocked Card", "refusalReasonCode": "5", "expected_error": ErrorType.BLOCKED_CARD},
        {"holder_name": "CARD_EXPIRED", "resultCode": "Refused", "refusalReason": "Expired Card", "refusalReasonCode": "6", "expected_error": ErrorType.EXPIRED_CARD},
        {"holder_name": "INVALID_AMOUNT", "resultCode": "Refused", "refusalReason": "Invalid Amount", "refusalReasonCode": "7", "expected_error": ErrorType.INVALID_AMOUNT},
        {"holder_name": "INVALID_CARD_NUMBER", "resultCode": "Refused", "refusalReason": "Invalid Card Number", "refusalReasonCode": "8", "expected_error": ErrorType.INVALID_CARD},
        {"holder_name": "ISSUER_UNAVAILABLE", "resultCode": "Refused", "refusalReason": "Issuer Unavailable", "refusalReasonCode": "9", "expected_error": ErrorType.OTHER},
        {"holder_name": "NOT_SUPPORTED", "resultCode": "Refused", "refusalReason": "Not supported", "refusalReasonCode": "10", "expected_error": ErrorType.NOT_SUPPORTED},
        {"holder_name": "NOT_3D_AUTHENTICATED", "resultCode": "Refused", "refusalReason": "3D Not Authenticated", "refusalReasonCode": "11", "expected_error": ErrorType.AUTHENTICATION_FAILURE},
        {"holder_name": "NOT_ENOUGH_BALANCE", "resultCode": "Refused", "refusalReason": "Not enough balance", "refusalReasonCode": "12", "expected_error": ErrorType.INSUFFICENT_FUNDS},
        {"holder_name": "ACQUIRER_FRAUD", "resultCode": "Refused", "refusalReason": "Acquirer Fraud", "refusalReasonCode": "14", "expected_error": ErrorType.FRAUD},
        {"holder_name": "CANCELLED", "resultCode": "Refused", "refusalReason": "Cancelled", "refusalReasonCode": "15", "expected_error": ErrorType.PAYMENT_CANCELLED},
        {"holder_name": "SHOPPER_CANCELLED", "resultCode": "Refused", "refusalReason": "Shopper Cancelled", "refusalReasonCode": "16", "expected_error": ErrorType.PAYMENT_CANCELLED_BY_CONSUMER},
        {"holder_name": "INVALID_PIN", "resultCode": "Refused", "refusalReason": "Invalid Pin", "refusalReasonCode": "17", "expected_error": ErrorType.INVALID_PIN},
        {"holder_name": "PIN_TRIES_EXCEEDED", "resultCode": "Refused", "refusalReason": "Pin tries exceeded", "refusalReasonCode": "18", "expected_error": ErrorType.PIN_TRIES_EXCEEDED},
        {"holder_name": "PIN_VALIDATION_NOT_POSSIBLE", "resultCode": "Refused", "refusalReason": "Pin validation not possible", "refusalReasonCode": "19", "expected_error": ErrorType.OTHER},
        {"holder_name": "FRAUD", "resultCode": "Refused", "refusalReason": "FRAUD", "refusalReasonCode": "20", "expected_error": ErrorType.FRAUD},
        {"holder_name": "NOT_SUBMITTED", "resultCode": "Refused", "refusalReason": "Not Submitted", "refusalReasonCode": "21", "expected_error": ErrorType.OTHER},
        {"holder_name": "FRAUD_CANCELLED", "resultCode": "Cancelled", "refusalReason": "FRAUD-CANCELLED", "refusalReasonCode": "22", "expected_error": ErrorType.FRAUD},
        {"holder_name": "TRANSACTION_NOT_PERMITTED", "resultCode": "Refused", "refusalReason": "Transaction Not Permitted", "refusalReasonCode": "23", "expected_error": ErrorType.NOT_SUPPORTED},
        {"holder_name": "CVC_DECLINED", "resultCode": "Refused", "refusalReason": "CVC Declined", "refusalReasonCode": "24", "expected_error": ErrorType.CVC_INVALID},
        {"holder_name": "RESTRICTED_CARD", "resultCode": "Refused", "refusalReason": "Restricted Card", "refusalReasonCode": "25", "expected_error": ErrorType.RESTRICTED_CARD},
        {"holder_name": "REVOCATION_OF_AUTH", "resultCode": "Refused", "refusalReason": "Revocation Of Auth", "refusalReasonCode": "26", "expected_error": ErrorType.STOP_PAYMENT},
        {"holder_name": "DECLINED_NON_GENERIC", "resultCode": "Refused", "refusalReason": "Declined Non Generic", "refusalReasonCode": "27", "expected_error": ErrorType.REFUSED},
        {"holder_name": "WITHDRAWAL_AMOUNT_EXCEEDED", "resultCode": "Refused", "refusalReason": "Withdrawal amount exceeded", "refusalReasonCode": "28", "expected_error": ErrorType.INSUFFICENT_FUNDS},
        {"holder_name": "WITHDRAWAL_COUNT_EXCEEDED", "resultCode": "Refused", "refusalReason": "Withdrawal count exceeded", "refusalReasonCode": "29", "expected_error": ErrorType.INSUFFICENT_FUNDS},
        {"holder_name": "ISSUER_SUSPECTED_FRAUD", "resultCode": "Refused", "refusalReason": "Issuer Suspected Fraud", "refusalReasonCode": "31", "expected_error": ErrorType.FRAUD},
        {"holder_name": "AVS_DECLINED", "resultCode": "Refused", "refusalReason": "AVS Declined", "refusalReasonCode": "32", "expected_error": ErrorType.AVS_DECLINE},
        {"holder_name": "PIN_REQUIRED", "resultCode": "Refused", "refusalReason": "Card requires online pin", "refusalReasonCode": "33", "expected_error": ErrorType.PIN_REQUIRED},
        {"holder_name": "NO_CHECKING_ACCOUNT", "resultCode": "Refused", "refusalReason": "No checking account available on Card", "refusalReasonCode": "34", "expected_error": ErrorType.BANK_ERROR},
        {"holder_name": "NO_SAVINGS_ACCOUNT", "resultCode": "Refused", "refusalReason": "No savings account available on Card", "refusalReasonCode": "35", "expected_error": ErrorType.BANK_ERROR},
        {"holder_name": "MOBILE_PIN_REQUIRED", "resultCode": "Refused", "refusalReason": "Mobile PIN required", "refusalReasonCode": "36", "expected_error": ErrorType.PIN_REQUIRED},
        {"holder_name": "CONTACTLESS_FALLBACK", "resultCode": "Refused", "refusalReason": "Contactless fallback", "refusalReasonCode": "37", "expected_error": ErrorType.CONTACTLESS_FALLBACK},
        {"holder_name": "AUTHENTICATION_REQUIRED", "resultCode": "Refused", "refusalReason": "Authentication required", "refusalReasonCode": "38", "expected_error": ErrorType.AUTHENTICATION_REQUIRED},
        {"holder_name": "RREQ_NOT_RECEIVED", "resultCode": "Refused", "refusalReason": "RReq not received from DS", "refusalReasonCode": "39", "expected_error": ErrorType.AUTHENTICATION_FAILURE},
        {"holder_name": "BAN_CURRENT_AID", "resultCode": "Refused", "refusalReason": "Current AID is in Penalty Box.", "refusalReasonCode": "40", "expected_error": ErrorType.OTHER},
        {"holder_name": "CVM_REQUIRED", "resultCode": "Refused", "refusalReason": "CVM Required Restart Payment", "refusalReasonCode": "41", "expected_error": ErrorType.PIN_REQUIRED},
        {"holder_name": "THREED_SECURE_ERROR", "resultCode": "Refused", "refusalReason": "3DS Authentication Error", "refusalReasonCode": "42", "expected_error": ErrorType.AUTHENTICATION_FAILURE},
        {"holder_name": "ONLINE_PIN_REQUIRED", "resultCode": "Refused", "refusalReason": "Online PIN required", "refusalReasonCode": "43", "expected_error": ErrorType.PIN_REQUIRED},
        {"holder_name": "TRY_ANOTHER_INTERFACE", "resultCode": "Refused", "refusalReason": "Try another interface", "refusalReasonCode": "44", "expected_error": ErrorType.OTHER},
        {"holder_name": "CHIP_DOWNGRADE_MODE", "resultCode": "Refused", "refusalReason": "Chip downgrade mode", "refusalReasonCode": "45", "expected_error": ErrorType.OTHER},
        {"holder_name": "ERPS_BLOCK", "resultCode": "Refused", "refusalReason": "Transaction blocked by Adyen to prevent excessive retry fees", "refusalReasonCode": "46", "expected_error": ErrorType.PROCESSOR_BLOCKED}
    ]

    # Initialize the SDK
    sdk = PaymentOrchestrationSDK.init({
        'is_test': True,
        'bt_api_key': 'test_bt_api_key',
        'provider_config': {
            'adyen': {
                'api_key': 'test_adyen_api_key',
                'merchant_account': 'test_merchant',
            }
        }
    })

    for test_case in test_cases:
        # Create mock response data
        mock_response_data = {
            "pspReference": "8837544667111111", 
            "merchantReference": "test_reference",
            "amount": {
                "value": 1,
                "currency": "USD"
            },
            "resultCode": test_case["resultCode"],
            "refusalReason": test_case["refusalReason"],
            "refusalReasonCode": test_case["refusalReasonCode"],
            "additionalData": {
                "refusalReasonRaw": f"DECLINED {test_case['refusalReason']}" if test_case["refusalReason"] else None
            }
        }

        # Create a mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_response.ok = True

        # Create a test transaction request
        transaction_request = TransactionRequest(
            reference='test_reference',
            type=RecurringType.ONE_TIME,
            amount=Amount(
                value=1,
                currency='USD'
            ),
            source=Source(
                type=SourceType.PROCESSOR_TOKEN,
                id='test_token_id',
                store_with_provider=False,
                holder_name=test_case['holder_name']
            ),
            customer=Customer(
                reference='test_customer_ref'
            )
        )

        # Mock the session.request method
        with patch('requests.request', return_value=mock_response) as mock_request:
            # For error cases, expect TransactionError with correct error code
            with pytest.raises(TransactionError) as exc_info:
                await sdk.adyen.transaction(transaction_request)
            
            error_response = exc_info.value.error_response
            assert error_response.error_codes[0].code == test_case["expected_error"].code

            # Verify the request was made
            mock_request.assert_called_once()
