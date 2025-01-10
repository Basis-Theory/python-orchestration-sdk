import os
import uuid
import pytest
import requests
from datetime import datetime
from unittest.mock import MagicMock, patch
from payment_orchestration_sdk import PaymentOrchestrationSDK
from payment_orchestration_sdk.models import (
    TransactionStatusCode,
    RecurringType,
    SourceType,
    ErrorCategory,
    ErrorType
)

# Expected error mappings for test verification
EXPECTED_ERROR_MAPPING = {
    "2": (ErrorType.REFUSED, ErrorCategory.PROCESSING_ERROR),  # Refused
    "3": (ErrorType.REFERRAL, ErrorCategory.PROCESSING_ERROR),  # Referral
    "4": (ErrorType.ACQUIRER_ERROR, ErrorCategory.OTHER),  # Acquirer Error
    "5": (ErrorType.BLOCKED_CARD, ErrorCategory.PAYMENT_METHOD_ERROR),  # Blocked Card
    "6": (ErrorType.EXPIRED_CARD, ErrorCategory.PAYMENT_METHOD_ERROR),  # Expired Card
    "7": (ErrorType.INVALID_AMOUNT, ErrorCategory.OTHER),  # Invalid Amount
    "8": (ErrorType.INVALID_CARD, ErrorCategory.PAYMENT_METHOD_ERROR),  # Invalid Card Number
    "9": (ErrorType.OTHER, ErrorCategory.OTHER),  # Issuer Unavailable
    "10": (ErrorType.NOT_SUPPORTED, ErrorCategory.PROCESSING_ERROR),  # Not supported
    "11": (ErrorType.AUTHENTICATION_FAILURE, ErrorCategory.PAYMENT_METHOD_ERROR),  # 3D Not Authenticated
    "12": (ErrorType.INSUFFICENT_FUNDS, ErrorCategory.PAYMENT_METHOD_ERROR),  # Not enough balance
    "14": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE),  # Acquirer Fraud
    "15": (ErrorType.PAYMENT_CANCELLED, ErrorCategory.OTHER),  # Cancelled
    "16": (ErrorType.PAYMENT_CANCELLED_BY_CONSUMER, ErrorCategory.PROCESSING_ERROR),  # Shopper Cancelled
    "17": (ErrorType.INVALID_PIN, ErrorCategory.PAYMENT_METHOD_ERROR),  # Invalid Pin
    "18": (ErrorType.PIN_TRIES_EXCEEDED, ErrorCategory.PAYMENT_METHOD_ERROR),  # Pin tries exceeded
    "20": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE),  # FRAUD
    "21": (ErrorType.OTHER, ErrorCategory.OTHER),  # Not Submitted
    "22": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE),  # FRAUD-CANCELLED
    "23": (ErrorType.NOT_SUPPORTED, ErrorCategory.PROCESSING_ERROR),  # Transaction Not Permitted
    "24": (ErrorType.CVC_INVALID, ErrorCategory.PAYMENT_METHOD_ERROR),  # CVC Declined
    "25": (ErrorType.RESTRICTED_CARD, ErrorCategory.PROCESSING_ERROR),  # Restricted Card
    "26": (ErrorType.STOP_PAYMENT, ErrorCategory.PROCESSING_ERROR),  # Revocation Of Auth
    "27": (ErrorType.OTHER, ErrorCategory.OTHER),  # Declined Non Generic
    "28": (ErrorType.INSUFFICENT_FUNDS, ErrorCategory.PROCESSING_ERROR),  # Withdrawal amount exceeded
    "29": (ErrorType.INSUFFICENT_FUNDS, ErrorCategory.PROCESSING_ERROR),  # Withdrawal count exceeded
    "31": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE),  # Issuer Suspected Fraud
    "32": (ErrorType.AVS_DECLINE, ErrorCategory.PROCESSING_ERROR),  # AVS Declined
    "33": (ErrorType.PIN_REQUIRED, ErrorCategory.PROCESSING_ERROR),  # Card requires online pin
    "34": (ErrorType.BANK_ERROR, ErrorCategory.PROCESSING_ERROR),  # No checking account available on Card
    "35": (ErrorType.BANK_ERROR, ErrorCategory.PROCESSING_ERROR),  # No savings account available on Card
    "36": (ErrorType.PIN_REQUIRED, ErrorCategory.PROCESSING_ERROR),  # Mobile pin required
    "37": (ErrorType.CONTACTLESS_FALLBACK, ErrorCategory.PROCESSING_ERROR),  # Contactless fallback
    "38": (ErrorType.AUTHENTICATION_REQUIRED, ErrorCategory.PROCESSING_ERROR),  # Authentication required
    "39": (ErrorType.AUTHENTICATION_FAILURE, ErrorCategory.AUTHENTICATION_ERROR),  # RReq not received from DS
    "40": (ErrorType.OTHER, ErrorCategory.OTHER),  # Current AID is in Penalty Box
    "41": (ErrorType.PIN_REQUIRED, ErrorCategory.PROCESSING_ERROR),  # CVM Required Restart Payment
    "42": (ErrorType.AUTHENTICATION_FAILURE, ErrorCategory.AUTHENTICATION_ERROR),  # 3DS Authentication Error
    "46": (ErrorType.PROCESSOR_BLOCKED, ErrorCategory.PROCESSING_ERROR),  # Transaction blocked by Adyen to prevent excessive retry fees
}

@pytest.mark.asyncio
async def test_successful_transaction():
    # Mock response data that matches Adyen's format
    mock_response_data = {
        "pspReference": "8837544667111111",
        "merchantReference": "test_reference",
        "amount": {
            "value": 1,
            "currency": "USD"
        },
        "resultCode": "Authorised",
        "paymentMethod": {
            "storedPaymentMethodId": "8415736847425855"
        },
        "additionalData": {
            "networkTxReference": "123456789",
        }
    }

    # Create a mock response using MagicMock
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.ok = True

    # Initialize the SDK
    sdk = PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': 'test_bt_api_key',
        'providerConfig': {
            'adyen': {
                'apiKey': 'test_adyen_api_key',
                'merchantAccount': 'test_merchant',
            }
        }
    })

    # Create a test transaction request with processor token
    transaction_request = {
        'reference': 'test_reference',
        'type': RecurringType.CARD_ON_FILE,
        'amount': {
            'value': 1,
            'currency': 'USD'
        },
        'source': {
            'type': SourceType.PROCESSOR_TOKEN,
            'id': 'test_token_id',
            'store_with_provider': True,
            'holderName': 'John Doe'
        },
        'customer': {
            'reference': 'test_customer_ref',
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

    # Mock the requests.request method
    with patch('payment_orchestration_sdk.utils.request_client.requests.request', return_value=mock_response) as mock_request:
        # Make the transaction request
        response = await sdk.adyen.transaction(transaction_request)

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'POST'
        assert call_args[1]['headers']['X-API-Key'] == 'test_adyen_api_key'
        assert call_args[1]['headers']['Content-Type'] == 'application/json'
        assert 'https://checkout-test.adyen.com/v71/payments' in call_args[1]['url']

        # Validate response structure
        assert isinstance(response, dict)
        assert response['id'] == mock_response_data['pspReference']
        assert response['reference'] == mock_response_data['merchantReference']
        
        # Validate amount
        assert response['amount']['value'] == mock_response_data['amount']['value']
        assert response['amount']['currency'] == mock_response_data['amount']['currency']
        
        # Validate status
        assert response['status']['code'] == TransactionStatusCode.AUTHORIZED
        assert response['status']['provider_code'] == mock_response_data['resultCode']
        
        # Validate source
        assert response['source']['type'] == transaction_request['source']['type']
        assert response['source']['id'] == transaction_request['source']['id']
        assert response['source']['provisioned']['id'] == mock_response_data['paymentMethod']['storedPaymentMethodId']
        
        # Validate networkTransactionId
        assert response['networkTransactionId'] == mock_response_data['additionalData']['networkTxReference']
        
        # Validate full provider response
        assert response['full_provider_response'] == mock_response_data
        
        # Validate created_at
        assert 'created_at' in response
        try:
            datetime.fromisoformat(response['created_at'].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("created_at is not a valid ISO datetime string")

@pytest.mark.asyncio
async def test_errors():
    # Define test cases mapping
    test_cases = [
        {"holderName": "UNKNOWN", "resultCode": "Error", "refusalReason": "Unknown", "refusalReasonCode": "0", "expected_error": (ErrorType.OTHER, ErrorCategory.OTHER)},
        {"holderName": "APPROVED", "resultCode": "Authorised", "refusalReason": None, "refusalReasonCode": "1", "expected_error": None},
        {"holderName": "DECLINED", "resultCode": "Refused", "refusalReason": "Refused", "refusalReasonCode": "2", "expected_error": (ErrorType.REFUSED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "REFERRAL", "resultCode": "Refused", "refusalReason": "Referral", "refusalReasonCode": "3", "expected_error": (ErrorType.REFERRAL, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "ERROR", "resultCode": "Error", "refusalReason": "Acquirer Error", "refusalReasonCode": "4", "expected_error": (ErrorType.ACQUIRER_ERROR, ErrorCategory.OTHER)},
        {"holderName": "BLOCK_CARD", "resultCode": "Refused", "refusalReason": "Blocked Card", "refusalReasonCode": "5", "expected_error": (ErrorType.BLOCKED_CARD, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "CARD_EXPIRED", "resultCode": "Refused", "refusalReason": "Expired Card", "refusalReasonCode": "6", "expected_error": (ErrorType.EXPIRED_CARD, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "INVALID_AMOUNT", "resultCode": "Refused", "refusalReason": "Invalid Amount", "refusalReasonCode": "7", "expected_error": (ErrorType.INVALID_AMOUNT, ErrorCategory.OTHER)},
        {"holderName": "INVALID_CARD_NUMBER", "resultCode": "Refused", "refusalReason": "Invalid Card Number", "refusalReasonCode": "8", "expected_error": (ErrorType.INVALID_CARD, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "ISSUER_UNAVAILABLE", "resultCode": "Refused", "refusalReason": "Issuer Unavailable", "refusalReasonCode": "9", "expected_error": (ErrorType.OTHER, ErrorCategory.OTHER)},
        {"holderName": "NOT_SUPPORTED", "resultCode": "Refused", "refusalReason": "Not supported", "refusalReasonCode": "10", "expected_error": (ErrorType.NOT_SUPPORTED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "NOT_3D_AUTHENTICATED", "resultCode": "Refused", "refusalReason": "3D Not Authenticated", "refusalReasonCode": "11", "expected_error": (ErrorType.AUTHENTICATION_FAILURE, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "NOT_ENOUGH_BALANCE", "resultCode": "Refused", "refusalReason": "Not enough balance", "refusalReasonCode": "12", "expected_error": (ErrorType.INSUFFICENT_FUNDS, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "PENDING", "resultCode": "Received", "refusalReason": None, "refusalReasonCode": "13", "expected_error": None},
        {"holderName": "ACQUIRER_FRAUD", "resultCode": "Refused", "refusalReason": "Acquirer Fraud", "refusalReasonCode": "14", "expected_error": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE)},
        {"holderName": "CANCELLED", "resultCode": "Refused", "refusalReason": "Cancelled", "refusalReasonCode": "15", "expected_error": (ErrorType.PAYMENT_CANCELLED, ErrorCategory.OTHER)},
        {"holderName": "SHOPPER_CANCELLED", "resultCode": "Refused", "refusalReason": "Shopper Cancelled", "refusalReasonCode": "16", "expected_error": (ErrorType.PAYMENT_CANCELLED_BY_CONSUMER, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "INVALID_PIN", "resultCode": "Refused", "refusalReason": "Invalid Pin", "refusalReasonCode": "17", "expected_error": (ErrorType.INVALID_PIN, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "PIN_TRIES_EXCEEDED", "resultCode": "Refused", "refusalReason": "Pin tries exceeded", "refusalReasonCode": "18", "expected_error": (ErrorType.PIN_TRIES_EXCEEDED, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "PIN_VALIDATION_NOT_POSSIBLE", "resultCode": "Refused", "refusalReason": "Pin validation not possible", "refusalReasonCode": "19", "expected_error": (ErrorType.OTHER, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "FRAUD", "resultCode": "Refused", "refusalReason": "FRAUD", "refusalReasonCode": "20", "expected_error": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE)},
        {"holderName": "NOT_SUBMITTED", "resultCode": "Refused", "refusalReason": "Not Submitted", "refusalReasonCode": "21", "expected_error": (ErrorType.OTHER, ErrorCategory.OTHER)},
        {"holderName": "FRAUD_CANCELLED", "resultCode": "Cancelled", "refusalReason": "FRAUD-CANCELLED", "refusalReasonCode": "22", "expected_error": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE)},
        {"holderName": "TRANSACTION_NOT_PERMITTED", "resultCode": "Refused", "refusalReason": "Transaction Not Permitted", "refusalReasonCode": "23", "expected_error": (ErrorType.NOT_SUPPORTED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "CVC_DECLINED", "resultCode": "Refused", "refusalReason": "CVC Declined", "refusalReasonCode": "24", "expected_error": (ErrorType.CVC_INVALID, ErrorCategory.PAYMENT_METHOD_ERROR)},
        {"holderName": "RESTRICTED_CARD", "resultCode": "Refused", "refusalReason": "Restricted Card", "refusalReasonCode": "25", "expected_error": (ErrorType.RESTRICTED_CARD, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "REVOCATION_OF_AUTH", "resultCode": "Refused", "refusalReason": "Revocation Of Auth", "refusalReasonCode": "26", "expected_error": (ErrorType.STOP_PAYMENT, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "DECLINED_NON_GENERIC", "resultCode": "Refused", "refusalReason": "Declined Non Generic", "refusalReasonCode": "27", "expected_error": (ErrorType.OTHER, ErrorCategory.OTHER)},
        {"holderName": "WITHDRAWAL_AMOUNT_EXCEEDED", "resultCode": "Refused", "refusalReason": "Withdrawal amount exceeded", "refusalReasonCode": "28", "expected_error": (ErrorType.INSUFFICENT_FUNDS, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "WITHDRAWAL_COUNT_EXCEEDED", "resultCode": "Refused", "refusalReason": "Withdrawal count exceeded", "refusalReasonCode": "29", "expected_error": (ErrorType.INSUFFICENT_FUNDS, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "PARTIALLY_APPROVED", "resultCode": "Authorised", "refusalReason": None, "refusalReasonCode": "30", "expected_error": None},
        {"holderName": "ISSUER_SUSPECTED_FRAUD", "resultCode": "Refused", "refusalReason": "Issuer Suspected Fraud", "refusalReasonCode": "31", "expected_error": (ErrorType.FRAUD, ErrorCategory.FRAUD_DECLINE)},
        {"holderName": "AVS_DECLINED", "resultCode": "Refused", "refusalReason": "AVS Declined", "refusalReasonCode": "32", "expected_error": (ErrorType.AVS_DECLINE, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "PIN_REQUIRED", "resultCode": "Refused", "refusalReason": "Card requires online pin", "refusalReasonCode": "33", "expected_error": (ErrorType.PIN_REQUIRED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "NO_CHECKING_ACCOUNT", "resultCode": "Refused", "refusalReason": "No checking account available on Card", "refusalReasonCode": "34", "expected_error": (ErrorType.BANK_ERROR, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "NO_SAVINGS_ACCOUNT", "resultCode": "Refused", "refusalReason": "No savings account available on Card", "refusalReasonCode": "35", "expected_error": (ErrorType.BANK_ERROR, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "MOBILE_PIN_REQUIRED", "resultCode": "Refused", "refusalReason": "Mobile PIN required", "refusalReasonCode": "36", "expected_error": (ErrorType.PIN_REQUIRED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "CONTACTLESS_FALLBACK", "resultCode": "Refused", "refusalReason": "Contactless fallback", "refusalReasonCode": "37", "expected_error": (ErrorType.CONTACTLESS_FALLBACK, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "AUTHENTICATION_REQUIRED", "resultCode": "Refused", "refusalReason": "Authentication required", "refusalReasonCode": "38", "expected_error": (ErrorType.AUTHENTICATION_REQUIRED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "RREQ_NOT_RECEIVED", "resultCode": "Refused", "refusalReason": "RReq not received from DS", "refusalReasonCode": "39", "expected_error": (ErrorType.AUTHENTICATION_FAILURE, ErrorCategory.AUTHENTICATION_ERROR)},
        {"holderName": "BAN_CURRENT_AID", "resultCode": "Refused", "refusalReason": "Current AID is in Penalty Box.", "refusalReasonCode": "40", "expected_error": (ErrorType.OTHER, ErrorCategory.OTHER)},
        {"holderName": "CVM_REQUIRED", "resultCode": "Refused", "refusalReason": "CVM Required Restart Payment", "refusalReasonCode": "41", "expected_error": (ErrorType.PIN_REQUIRED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "THREED_SECURE_ERROR", "resultCode": "Refused", "refusalReason": "3DS Authentication Error", "refusalReasonCode": "42", "expected_error": (ErrorType.AUTHENTICATION_FAILURE, ErrorCategory.AUTHENTICATION_ERROR)},
        {"holderName": "ONLINE_PIN_REQUIRED", "resultCode": "Refused", "refusalReason": "Online PIN required", "refusalReasonCode": "43", "expected_error": (ErrorType.PIN_REQUIRED, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "TRY_ANOTHER_INTERFACE", "resultCode": "Refused", "refusalReason": "Try another interface", "refusalReasonCode": "44", "expected_error": (ErrorType.OTHER, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "CHIP_DOWNGRADE_MODE", "resultCode": "Refused", "refusalReason": "Chip downgrade mode", "refusalReasonCode": "45", "expected_error": (ErrorType.OTHER, ErrorCategory.PROCESSING_ERROR)},
        {"holderName": "ERPS_BLOCK", "resultCode": "Refused", "refusalReason": "Transaction blocked by Adyen to prevent excessive retry fees", "refusalReasonCode": "46", "expected_error": (ErrorType.PROCESSOR_BLOCKED, ErrorCategory.PROCESSING_ERROR)}
    ]

    # Initialize the SDK
    sdk = PaymentOrchestrationSDK.init({
        'isTest': True,
        'btApiKey': 'test_bt_api_key',
        'providerConfig': {
            'adyen': {
                'apiKey': 'test_adyen_api_key',
                'merchantAccount': 'test_merchant',
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
        transaction_request = {
            'reference': 'test_reference',
            'type': RecurringType.ONE_TIME,
            'amount': {
                'value': 1,
                'currency': 'USD'
            },
            'source': {
                'type': SourceType.PROCESSOR_TOKEN,
                'id': 'test_token_id',
                'store_with_provider': False,
                'holderName': test_case['holderName']
            },
            'customer': {
                'reference': 'test_customer_ref'
            }
        }

        # Mock the requests.request method
        with patch('payment_orchestration_sdk.utils.request_client.requests.request', return_value=mock_response) as mock_request:
            # Make the transaction request
            response = await sdk.adyen.transaction(transaction_request)

            # Verify the request was made with correct parameters
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]['method'] == 'POST'
            assert call_args[1]['headers']['X-API-Key'] == 'test_adyen_api_key'
            assert call_args[1]['headers']['Content-Type'] == 'application/json'
            assert 'https://checkout-test.adyen.com/v71/payments' in call_args[1]['url']

            # For successful transactions
            if test_case["resultCode"] == "Authorised":
                assert "status" in response
                assert response["status"]["code"] == TransactionStatusCode.AUTHORIZED
                assert response["status"]["provider_code"] == "Authorised"
                continue

            # For received/pending transactions
            if test_case["resultCode"] == "Received":
                assert "status" in response
                assert response["status"]["code"] == TransactionStatusCode.RECEIVED
                assert response["status"]["provider_code"] == "Received"
                continue

            # For error/refused transactions
            assert "error_codes" in response
            assert len(response["error_codes"]) == 1
            assert "provider_errors" in response
            if test_case["refusalReason"]:
                assert response["provider_errors"][0] == test_case["refusalReason"]

            # Verify the error mapping
            if test_case["expected_error"]:
                error_type, error_category = test_case["expected_error"]
                assert response["error_codes"][0]["code"] == error_type
                assert response["error_codes"][0]["category"] == error_category

            # Verify full provider response is included
            assert response["full_provider_response"] == mock_response_data
