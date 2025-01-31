from typing import Dict, Any, Tuple, Optional, Union, cast
from datetime import datetime, timezone
import requests
from deepmerge import always_merger
from ..models import (
    TransactionRequest,
    Amount,
    Source,
    SourceType,
    Customer,
    Address,
    StatementDescription,
    ThreeDS,
    RecurringType,
    TransactionStatusCode,
    ErrorType,
    ErrorCategory
)
from ..exceptions import ValidationError, ProcessingError
from ..utils.model_utils import create_transaction_request, validate_required_fields
from ..utils.request_client import RequestClient


RECURRING_TYPE_MAPPING = {
    RecurringType.ONE_TIME: None,
    RecurringType.CARD_ON_FILE: "CardOnFile",
    RecurringType.SUBSCRIPTION: "Subscription",
    RecurringType.UNSCHEDULED: "UnscheduledCardOnFile"
}


# Map Adyen resultCode to our status codes
STATUS_CODE_MAPPING = {
    "Authorised": TransactionStatusCode.AUTHORIZED,         # Adyen: Authorised - Payment was successfully authorized
    "Pending": TransactionStatusCode.PENDING,              # Adyen: Pending - Payment is pending, waiting for completion
    "Error": TransactionStatusCode.DECLINED,               # Adyen: Error - Technical error occurred
    "Refused": TransactionStatusCode.DECLINED,             # Adyen: Refused - Payment was refused
    "Cancelled": TransactionStatusCode.CANCELLED,          # Adyen: Cancelled - Payment was cancelled
    "ChallengeShopper": TransactionStatusCode.CHALLENGE_SHOPPER,  # Adyen: ChallengeShopper - 3DS2 challenge required
    "Received": TransactionStatusCode.RECEIVED,            # Adyen: Received - Payment was received
    "PartiallyAuthorised": TransactionStatusCode.PARTIALLY_AUTHORIZED  # Adyen: PartiallyAuthorised - Only part of the amount was authorized
}


# Mapping of Adyen refusal reason codes to our error types
ERROR_CODE_MAPPING = {
    "2": ErrorType.REFUSED,  # Refused
    "3": ErrorType.REFERRAL,  # Referral
    "4": ErrorType.ACQUIRER_ERROR,  # Acquirer Error
    "5": ErrorType.BLOCKED_CARD,  # Blocked Card
    "6": ErrorType.EXPIRED_CARD,  # Expired Card
    "7": ErrorType.INVALID_AMOUNT,  # Invalid Amount
    "8": ErrorType.INVALID_CARD,  # Invalid Card Number
    "9": ErrorType.OTHER,  # Issuer Unavailable
    "10": ErrorType.NOT_SUPPORTED,  # Not supported
    "11": ErrorType.AUTHENTICATION_FAILURE,  # 3D Not Authenticated
    "12": ErrorType.INSUFFICENT_FUNDS,  # Not enough balance
    "14": ErrorType.FRAUD,  # Acquirer Fraud
    "15": ErrorType.PAYMENT_CANCELLED,  # Cancelled
    "16": ErrorType.PAYMENT_CANCELLED_BY_CONSUMER,  # Shopper Cancelled
    "17": ErrorType.INVALID_PIN,  # Invalid Pin
    "18": ErrorType.PIN_TRIES_EXCEEDED,  # Pin tries exceeded
    "19": ErrorType.OTHER,  # Pin validation not possible
    "20": ErrorType.FRAUD,  # FRAUD
    "21": ErrorType.OTHER,  # Not Submitted
    "22": ErrorType.FRAUD,  # FRAUD-CANCELLED
    "23": ErrorType.NOT_SUPPORTED,  # Transaction Not Permitted
    "24": ErrorType.CVC_INVALID,  # CVC Declined
    "25": ErrorType.RESTRICTED_CARD,  # Restricted Card
    "26": ErrorType.STOP_PAYMENT,  # Revocation Of Auth
    "27": ErrorType.REFUSED,  # Declined Non Generic
    "28": ErrorType.INSUFFICENT_FUNDS,  # Withdrawal amount exceeded
    "29": ErrorType.INSUFFICENT_FUNDS,  # Withdrawal count exceeded
    "31": ErrorType.FRAUD,  # Issuer Suspected Fraud
    "32": ErrorType.AVS_DECLINE,  # AVS Declined
    "33": ErrorType.PIN_REQUIRED,  # Card requires online pin
    "34": ErrorType.BANK_ERROR,  # No checking account available on Card
    "35": ErrorType.BANK_ERROR,  # No savings account available on Card
    "36": ErrorType.PIN_REQUIRED,  # Mobile pin required
    "37": ErrorType.CONTACTLESS_FALLBACK,  # Contactless fallback
    "38": ErrorType.AUTHENTICATION_REQUIRED,  # Authentication required
    "39": ErrorType.AUTHENTICATION_FAILURE,  # RReq not received from DS
    "40": ErrorType.OTHER,  # Current AID is in Penalty Box
    "41": ErrorType.PIN_REQUIRED,  # CVM Required Restart Payment
    "42": ErrorType.AUTHENTICATION_FAILURE,  # 3DS Authentication Error
    "43": ErrorType.PIN_REQUIRED,  # Online PIN required
    "44": ErrorType.OTHER,  # Try another interface
    "45": ErrorType.OTHER,  # Chip downgrade mode
    "46": ErrorType.PROCESSOR_BLOCKED,  # Transaction blocked by Adyen to prevent excessive retry fees
}


class AdyenClient:
    def __init__(self, api_key: str, merchant_account: str, is_test: bool, bt_api_key: str, production_prefix: str):
        self.api_key = api_key
        self.merchant_account = merchant_account
        self.base_url = "https://checkout-test.adyen.com/v71" if is_test else f"https://{production_prefix}-checkout-live.adyenpayments.com/checkout/v71"
        self.request_client = RequestClient(bt_api_key)

    def _get_status_code(self, adyen_result_code: Optional[str]) -> TransactionStatusCode:
        """Map Adyen result code to our status code."""
        if not adyen_result_code:
            return TransactionStatusCode.DECLINED
        return STATUS_CODE_MAPPING.get(adyen_result_code, TransactionStatusCode.DECLINED)

    def _transform_to_adyen_payload(self, request: TransactionRequest) -> Dict[str, Any]:
        """Transform SDK request to Adyen payload format."""
        payload: Dict[str, Any] = {
            "amount": {
                "value": request.amount.value,
                "currency": request.amount.currency
            },
            "merchantAccount": self.merchant_account,
            "shopperInteraction": "ContAuth" if request.merchant_initiated else "Ecommerce",
            "storePaymentMethod": request.source.store_with_provider,
        }

        if request.metadata:
            payload["metadata"] = request.metadata

        # Add reference if provided
        if request.reference:
            payload["reference"] = request.reference

        # Add recurring type if provided
        if request.type:
            recurring_type = RECURRING_TYPE_MAPPING.get(request.type)
            if recurring_type:
                payload["recurringProcessingModel"] = recurring_type

        # Process source based on type
        payment_method: Dict[str, Any] = {"type": "scheme"}
        
        if request.source.type == SourceType.PROCESSOR_TOKEN:
            payment_method["storedPaymentMethodId"] = request.source.id
            if request.source.holder_name:
                payment_method["holderName"] = request.source.holder_name
        elif request.source.type in [SourceType.BASIS_THEORY_TOKEN, SourceType.BASIS_THEORY_TOKEN_INTENT]:
            # Add card data with Basis Theory expressions
            token_prefix = "token_intent" if request.source.type == SourceType.BASIS_THEORY_TOKEN_INTENT else "token"
            payment_method.update({
                "number": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.number'}}}}",
                "expiryMonth": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.expiration_month'}}}}",
                "expiryYear": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.expiration_year'}}}}",
                "cvc": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.cvc'}}}}"
            })
            if request.source.holder_name:
                payment_method["holderName"] = request.source.holder_name

        payload["paymentMethod"] = payment_method

        # Add customer information
        if request.customer:
            if request.customer.reference:
                payload["shopperReference"] = request.customer.reference

            # Map name fields
            if request.customer.first_name or request.customer.last_name:
                shopper_name: Dict[str, str] = {}
                if request.customer.first_name:
                    shopper_name["firstName"] = request.customer.first_name
                if request.customer.last_name:
                    shopper_name["lastName"] = request.customer.last_name
                payload["shopperName"] = shopper_name

            # Map email directly
            if request.customer.email:
                payload["shopperEmail"] = request.customer.email

            # Map address fields
            if request.customer.address:
                address = request.customer.address
                if any([address.address_line1, address.city, address.state, address.zip, address.country]):
                    billing_address: Dict[str, str] = {}

                    # Map address_line1 to street
                    if address.address_line1:
                        billing_address["street"] = address.address_line1

                    if address.city:
                        billing_address["city"] = address.city

                    if address.state:
                        billing_address["stateOrProvince"] = address.state

                    if address.zip:
                        billing_address["postalCode"] = address.zip

                    if address.country:
                        billing_address["country"] = address.country

                    payload["billingAddress"] = billing_address

        # Map statement description (only name, city is not mapped as per CSV)
        if request.statement_description and request.statement_description.name:
            payload["shopperStatement"] = request.statement_description.name

        # Map 3DS information
        if request.three_ds:
            three_ds_data: Dict[str, str] = {}

            if request.three_ds.eci:
                three_ds_data["eci"] = request.three_ds.eci

            if request.three_ds.authentication_value:
                three_ds_data["authenticationValue"] = request.three_ds.authentication_value

            if request.three_ds.xid:
                three_ds_data["xid"] = request.three_ds.xid

            if request.three_ds.version:
                three_ds_data["threeDSVersion"] = request.three_ds.version

            if three_ds_data:
                payload["additionalData"] = {"threeDSecure": three_ds_data}

        # Override/merge any provider properties if specified
        if request.override_provider_properties:
            payload = always_merger.merge(payload, request.override_provider_properties)

        return payload

    def _transform_adyen_response(self, response_data: Dict[str, Any], request: TransactionRequest) -> Dict[str, Any]:
        """Transform Adyen response to our standardized format."""
        return {
            "id": response_data.get("pspReference"),
            "reference": response_data.get("merchantReference"),
            "amount": {
                "value": response_data.get("amount", {}).get("value"),
                "currency": response_data.get("amount", {}).get("currency")
            },
            "status": {
                "code": self._get_status_code(response_data.get("resultCode")),
                "provider_code": response_data.get("resultCode")
            },
            "source": {
                "type": request.source.type,
                "id": request.source.id,
                "provisioned": {
                    "id": response_data.get("paymentMethod", {}).get("storedPaymentMethodId") or 
                         response_data.get("additionalData", {}).get("recurring.recurringDetailReference")
                } if (response_data.get("paymentMethod", {}).get("storedPaymentMethodId") or 
                      response_data.get("additionalData", {}).get("recurring.recurringDetailReference")) else None
            },
            "network_transaction_id": response_data.get("additionalData", {}).get("networkTxReference"),
            "full_provider_response": response_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def _transform_error_response(self, response: requests.Response, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform error responses to our standardized format.
        
        Args:
            response: The HTTP response object
            response_data: The parsed JSON response data
            
        Returns:
            Dict[str, Any]: Standardized error response
        """
        # Map HTTP status codes to error types
        if response.status_code == 401:
            error_type = ErrorType.INVALID_API_KEY
        elif response.status_code == 403:
            error_type = ErrorType.UNAUTHORIZED
        # Handle Adyen-specific error codes for declined transactions
        elif response_data.get("resultCode") in ["Refused", "Error", "Cancelled"]:
            refusal_code = response_data.get("refusalReasonCode", "")
            error_type = ERROR_CODE_MAPPING.get(refusal_code, ErrorType.OTHER)
        else:
            error_type = ErrorType.OTHER

        return {
            "error_codes": [
                {
                    "category": error_type.category,
                    "code": error_type.code
                }
            ],
            "provider_errors": [response_data.get("refusalReason") or response_data.get("message", "")],
            "full_provider_response": response_data
        }

    async def transaction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment transaction through Adyen's API directly or via Basis Theory's proxy."""
        validate_required_fields(request_data)

        # Convert the dictionary to our internal TransactionRequest model
        request = create_transaction_request(request_data)

        # Transform to Adyen's format
        payload = self._transform_to_adyen_payload(request)

        # Set up common headers
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        # Make the request (using proxy for BT tokens, direct for processor tokens)
        try:
            response = self.request_client.request(
                url=f"{self.base_url}/payments",
                method="POST",
                headers=headers,
                data=payload,
                use_bt_proxy=request.source.type != SourceType.PROCESSOR_TOKEN
            )
        except requests.exceptions.HTTPError as e:
            # Check if this is a BT error
            if hasattr(e, 'bt_error_response'):
                return e.bt_error_response
            # Handle HTTP errors (like 401, 403, etc.)
            return self._transform_error_response(e.response, e.response.json())

        response_data = response.json()

        # Check if it's an error response (non-200 status code or Adyen error)
        if not response.ok or response_data.get("resultCode") in ["Refused", "Error", "Cancelled"]:
            return self._transform_error_response(response, response_data)

        # Transform the successful response to our format
        return self._transform_adyen_response(response_data, request)
