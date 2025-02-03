from typing import Dict, Any, Tuple, Optional, Union, cast
from datetime import datetime, timezone
import requests
import os
import json
from json.decoder import JSONDecodeError

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
    ErrorCategory,
    RefundRequest,
    RefundResponse,
    TransactionStatus,
    ErrorResponse,
    ErrorCode
)
from orchestration_sdk.exceptions import TransactionException
from ..utils.model_utils import create_transaction_request, validate_required_fields
from ..utils.request_client import RequestClient


RECURRING_TYPE_MAPPING = {
    RecurringType.ONE_TIME: "Regular",
    RecurringType.CARD_ON_FILE: "CardOnFile",
    RecurringType.SUBSCRIPTION: "Recurring",
    RecurringType.UNSCHEDULED: "Unscheduled"
}

# Map Checkout.com status to our status codes
STATUS_CODE_MAPPING = {
    "Authorized": TransactionStatusCode.AUTHORIZED,
    "Pending": TransactionStatusCode.PENDING,
    "Card Verified": TransactionStatusCode.CARD_VERIFIED,
    "Declined": TransactionStatusCode.DECLINED,
    "Retry Scheduled": TransactionStatusCode.RETRY_SCHEDULED
}

# Mapping of Checkout.com error codes to our error types
ERROR_CODE_MAPPING = {
    "card_authorization_failed": ErrorType.REFUSED,
    "card_disabled": ErrorType.BLOCKED_CARD,
    "card_expired": ErrorType.EXPIRED_CARD,
    "card_expiry_month_invalid": ErrorType.INVALID_CARD,
    "card_expiry_month_required": ErrorType.INVALID_CARD,
    "card_expiry_year_invalid": ErrorType.INVALID_CARD,
    "card_expiry_year_required": ErrorType.INVALID_CARD,
    "expiry_date_format_invalid": ErrorType.INVALID_CARD,
    "card_not_found": ErrorType.INVALID_CARD,
    "card_number_invalid": ErrorType.INVALID_CARD,
    "card_number_required": ErrorType.INVALID_CARD,
    "issuer_network_unavailable": ErrorType.OTHER,
    "card_not_eligible_domestic_money_transfer": ErrorType.NOT_SUPPORTED,
    "card_not_eligible_cross_border_money_transfer": ErrorType.NOT_SUPPORTED,
    "card_not_eligible_domestic_non_money_transfer": ErrorType.NOT_SUPPORTED,
    "card_not_eligible_cross_border_non_money_transfer": ErrorType.NOT_SUPPORTED,
    "card_not_eligible_domestic_online_gambling": ErrorType.NOT_SUPPORTED,
    "card_not_eligible_cross_border_online_gambling": ErrorType.NOT_SUPPORTED,
    "3ds_malfunction": ErrorType.AUTHENTICATION_FAILURE,
    "3ds_not_enabled_for_card": ErrorType.AUTHENTICATION_FAILURE,
    "3ds_not_supported": ErrorType.AUTHENTICATION_FAILURE,
    "3ds_not_configured": ErrorType.AUTHENTICATION_FAILURE,
    "3ds_payment_required": ErrorType.AUTHENTICATION_FAILURE,
    "3ds_version_invalid": ErrorType.AUTHENTICATION_FAILURE,
    "3ds_version_not_supported": ErrorType.AUTHENTICATION_FAILURE,
    "amount_exceeds_balance": ErrorType.INSUFFICENT_FUNDS,
    "amount_limit_exceeded": ErrorType.INSUFFICENT_FUNDS,
    "payment_expired": ErrorType.PAYMENT_CANCELLED,
    "cvv_invalid": ErrorType.CVC_INVALID,
    "processing_error": ErrorType.REFUSED,
    "velocity_amount_limit_exceeded": ErrorType.INSUFFICENT_FUNDS,
    "velocity_count_limit_exceeded": ErrorType.INSUFFICENT_FUNDS,
    "address_invalid": ErrorType.AVS_DECLINE,
    "city_invalid": ErrorType.AVS_DECLINE,
    "country_address_invalid": ErrorType.AVS_DECLINE,
    "country_invalid": ErrorType.AVS_DECLINE,
    "country_phone_code_invalid": ErrorType.AVS_DECLINE,
    "country_phone_code_length_invalid": ErrorType.AVS_DECLINE,
    "phone_number_invalid": ErrorType.AVS_DECLINE,
    "phone_number_length_invalid": ErrorType.AVS_DECLINE,
    "zip_invalid": ErrorType.AVS_DECLINE,
    "action_failure_limit_exceeded": ErrorType.PROCESSOR_BLOCKED,
    "token_expired": ErrorType.OTHER,
    "token_in_use": ErrorType.OTHER,
    "token_invalid": ErrorType.OTHER,
    "token_used": ErrorType.OTHER,
    "capture_value_greater_than_authorized": ErrorType.OTHER,
    "capture_value_greater_than_remaining_authorized": ErrorType.OTHER,
    "card_holder_invalid": ErrorType.OTHER,
    "previous_payment_id_invalid": ErrorType.OTHER,
    "processing_channel_id_required": ErrorType.CONFIGURATION_ERROR,
    "success_url_required": ErrorType.CONFIGURATION_ERROR,
    "source_token_invalid": ErrorType.INVALID_SOURCE_TOKEN,
    "aft_processor_not_matched": ErrorType.OTHER,
    "amount_invalid": ErrorType.OTHER,
    "api_calls_quota_exceeded": ErrorType.OTHER,
    "billing_descriptor_city_invalid": ErrorType.OTHER,
    "billing_descriptor_city_required": ErrorType.OTHER,
    "billing_descriptor_name_invalid": ErrorType.OTHER,
    "billing_descriptor_name_required": ErrorType.OTHER,
    "business_invalid": ErrorType.OTHER,
    "business_settings_missing": ErrorType.OTHER,
    "channel_details_invalid": ErrorType.OTHER,
    "channel_url_missing": ErrorType.OTHER,
    "charge_details_invalid": ErrorType.OTHER,
    "currency_invalid": ErrorType.OTHER,
    "currency_required": ErrorType.OTHER,
    "customer_already_exists": ErrorType.OTHER,
    "customer_email_invalid": ErrorType.OTHER,
    "customer_id_invalid": ErrorType.OTHER,
    "customer_not_found": ErrorType.OTHER,
    "customer_number_invalid": ErrorType.OTHER,
    "customer_plan_edit_failed": ErrorType.OTHER,
    "customer_plan_id_invalid": ErrorType.OTHER,
    "email_in_use": ErrorType.OTHER,
    "email_invalid": ErrorType.OTHER,
    "email_required": ErrorType.OTHER,
    "endpoint_invalid": ErrorType.OTHER,
    "fail_url_invalid": ErrorType.OTHER,
    "ip_address_invalid": ErrorType.OTHER,
    "metadata_key_invalid": ErrorType.OTHER,
    "no_authorization_enabled_processors_available": ErrorType.OTHER,
    "parameter_invalid": ErrorType.OTHER,
    "payment_invalid": ErrorType.OTHER,
    "payment_method_not_supported": ErrorType.OTHER,
    "payment_source_required": ErrorType.OTHER,
    "payment_type_invalid": ErrorType.OTHER,
    "processing_key_required": ErrorType.OTHER,
    "processing_value_required": ErrorType.OTHER,
    "recurring_plan_exists": ErrorType.OTHER,
    "recurring_plan_not_exist": ErrorType.OTHER,
    "recurring_plan_removal_failed": ErrorType.OTHER,
    "request_invalid": ErrorType.OTHER,
    "request_json_invalid": ErrorType.OTHER,
    "risk_enabled_required": ErrorType.OTHER,
    "server_api_not_allowed": ErrorType.OTHER,
    "source_email_invalid": ErrorType.OTHER,
    "source_email_required": ErrorType.OTHER,
    "source_id_invalid": ErrorType.OTHER,
    "source_id_or_email_required": ErrorType.OTHER,
    "source_id_required": ErrorType.OTHER,
    "source_id_unknown": ErrorType.OTHER,
    "source_invalid": ErrorType.OTHER,
    "source_or_destination_required": ErrorType.OTHER,
    "source_token_invalid": ErrorType.OTHER,
    "source_token_required": ErrorType.OTHER,
    "source_token_type_required": ErrorType.OTHER,
    "source_token_type_invalid": ErrorType.OTHER,
    "source_type_required": ErrorType.OTHER,
    "sub_entities_count_invalid": ErrorType.OTHER,
    "success_url_invalid": ErrorType.OTHER,
    "token_required": ErrorType.OTHER,
    "token_type_required": ErrorType.OTHER,
    "void_amount_invalid": ErrorType.OTHER,
    "refund_amount_exceeds_balance": ErrorType.REFUND_REFUND_AMOUNT_EXCEEDS_BALANCE,
    "refund_authorization_declined": ErrorType.REFUND_DECLINED
}


class CheckoutClient:
    def __init__(self, private_key: str, processing_channel: str, is_test: bool, bt_api_key: str):
        self.api_key = private_key
        self.processing_channel = processing_channel
        self.base_url = "https://api.sandbox.checkout.com" if is_test else "https://api.checkout.com"
        self.request_client = RequestClient(bt_api_key)

    def _get_status_code(self, checkout_status: Optional[str]) -> TransactionStatusCode:
        """Map Checkout.com status to our status code."""
        if not checkout_status:
            return TransactionStatusCode.DECLINED
        return STATUS_CODE_MAPPING.get(checkout_status, TransactionStatusCode.DECLINED)

    def _transform_to_checkout_payload(self, request: TransactionRequest) -> Dict[str, Any]:
        """Transform SDK request to Checkout.com payload format."""
        
        payload: Dict[str, Any] = { 
            "amount": request.amount.value,
            "currency": request.amount.currency,
            "merchant_initiated": request.merchant_initiated,
            "processing_channel_id": self.processing_channel,
            "reference": request.reference
        }

        if request.type:
            payload["payment_type"] = RECURRING_TYPE_MAPPING.get(request.type)

        # Process source based on type
        if request.source.type == SourceType.PROCESSOR_TOKEN:
            payload["source"] = {
                "type": "id",
                "id": request.source.id
            }
        elif request.source.type in [SourceType.BASIS_THEORY_TOKEN, SourceType.BASIS_THEORY_TOKEN_INTENT]:
            # Add card data with Basis Theory expressions
            token_prefix = "token_intent" if request.source.type == SourceType.BASIS_THEORY_TOKEN_INTENT else "token"
            source_data: Dict[str, Any] = {
                "type": "card",
                "number": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.number'}}}}",
                "expiry_month": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.expiration_month'}}}}",
                "expiry_year": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.expiration_year'}}}}",
                "cvv": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.cvc'}}}}",
                "store_for_future_use": request.source.store_with_provider
            }
            payload["source"] = source_data

        # Add customer information if provided
        if request.customer:
            customer_data: Dict[str, Any] = {}
            if request.customer.first_name or request.customer.last_name:
                name_parts = []
                if request.customer.first_name:
                    name_parts.append(request.customer.first_name)
                if request.customer.last_name:
                    name_parts.append(request.customer.last_name)
                customer_data["name"] = " ".join(name_parts)

            if request.customer.email:
                customer_data["email"] = request.customer.email
            
            payload["customer"] = customer_data

            # Add billing address if provided
            if request.customer.address and "source" in payload:
                billing_address: Dict[str, str] = {}
                if request.customer.address.address_line1:
                    billing_address["address_line1"] = request.customer.address.address_line1
                if request.customer.address.address_line2:
                    billing_address["address_line2"] = request.customer.address.address_line2
                if request.customer.address.city:
                    billing_address["city"] = request.customer.address.city
                if request.customer.address.state:
                    billing_address["state"] = request.customer.address.state
                if request.customer.address.zip:
                    billing_address["zip"] = request.customer.address.zip
                if request.customer.address.country:
                    billing_address["country"] = request.customer.address.country
                
                source = cast(Dict[str, Any], payload["source"])
                source["billing_address"] = billing_address

        # Add statement descriptor if provided
        if request.statement_description and "source" in payload:
            source = cast(Dict[str, Any], payload["source"])
            billing_descriptor: Dict[str, str] = {}
            if request.statement_description.name:
                billing_descriptor["name"] = request.statement_description.name
            if request.statement_description.city:
                billing_descriptor["city"] = request.statement_description.city
            source["billing_descriptor"] = billing_descriptor

        # Add 3DS information if provided
        if request.three_ds:
            three_ds_data: Dict[str, str] = {}
            if request.three_ds.eci:
                three_ds_data["eci"] = request.three_ds.eci
            if request.three_ds.authentication_value:
                three_ds_data["cryptogram"] = request.three_ds.authentication_value
            if request.three_ds.xid:
                three_ds_data["xid"] = request.three_ds.xid
            if request.three_ds.version:
                three_ds_data["version"] = request.three_ds.version
            payload["3ds"] = three_ds_data

        return payload

    def _transform_checkout_response(self, response_data: Dict[str, Any], request: TransactionRequest) -> Dict[str, Any]:
        """Transform Checkout.com response to our standardized format."""
        return {
            "id": response_data.get("id"),
            "reference": response_data.get("reference"),
            "amount": {
                "value": response_data.get("amount"),
                "currency": response_data.get("currency")
            },
            "status": {
                "code": self._get_status_code(response_data.get("status")),
                "provider_code": response_data.get("status")
            },
            "source": {
                "type": request.source.type,
                "id": request.source.id,
                "provisioned": {
                    "id": response_data.get("source", {}).get("id")
                } if response_data.get("source", {}).get("id") else None
            },
            "full_provider_response": response_data,
            "created_at": datetime.fromisoformat(response_data["processed_on"].split(".")[0] + "+00:00").isoformat("T", "milliseconds") if response_data.get("processed_on") else None,
            "networkTransactionId": response_data.get("processing", {}).get("acquirer_transaction_id")
        }

    def _get_error_code(self, error: ErrorType) -> Dict[str, Any]:
        return {
            "category": error.category,
            "code": error.code
        }

    def _get_error_code_object(self, error: ErrorType) -> ErrorCode:
        return ErrorCode(
            category=error.category,
            code=error.code
        )


    def _transform_error_response(self, response, error_data=None):
        """Transform error response from Checkout.com to SDK format."""
        error_codes = []
        
        if response.status_code == 401:
            error_codes.append(self._get_error_code(ErrorType.INVALID_API_KEY))
        elif response.status_code == 403:
            error_codes.append(self._get_error_code(ErrorType.UNAUTHORIZED))
        elif error_data is not None:
            for error_code in error_data.get('error_codes', []):
                mapped_error = ERROR_CODE_MAPPING.get(error_code, ErrorType.OTHER)
                error_codes.append(self._get_error_code(mapped_error))

            if not error_codes:
                error_codes.append(self._get_error_code(ErrorType.OTHER))
        else:
            error_codes.append(self._get_error_code(ErrorType.OTHER))
        
        return {
            "error_codes": error_codes,
            "provider_errors": error_data.get('error_codes', []) if error_data else [],
            "full_provider_response": error_data
        }

    def _transform_error_response_object(self, response, error_data=None) -> ErrorResponse:
        """Transform error response from Checkout.com to SDK format."""
        error_codes = []
        
        if response.status_code == 401:
            error_codes.append(self._get_error_code_object(ErrorType.INVALID_API_KEY))
        elif response.status_code == 403:
            error_codes.append(self._get_error_code_object(ErrorType.UNAUTHORIZED))
        elif error_data is not None:
            for error_code in error_data.get('error_codes', []):
                mapped_error = ERROR_CODE_MAPPING.get(error_code, ErrorType.OTHER)
                error_codes.append(self._get_error_code_object(mapped_error))

            if not error_codes:
                error_codes.append(self._get_error_code_object(ErrorType.OTHER))
        else:
            error_codes.append(self._get_error_code_object(ErrorType.OTHER))
        
        return ErrorResponse(
            error_codes=error_codes,
            provider_errors=error_data.get('error_codes', []) if error_data else [],
            full_provider_response=error_data
        )


    async def transaction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment transaction through Checkout.com's API directly or via Basis Theory's proxy."""
        validate_required_fields(request_data)

        request = create_transaction_request(request_data)

        # Transform request to Checkout.com format
        payload = self._transform_to_checkout_payload(request)
        
        # Set up common headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Make request to Checkout.com
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
            
            try:
                error_data = e.response.json()
            except:
                error_data = None

            raise TransactionException(self._transform_error_response_object(e.response, error_data))

        # Transform response to SDK format
        return self._transform_checkout_response(response.json(), request)

    async def refund_transaction(self, refund_request: RefundRequest) -> RefundResponse:
        """
        Refund a payment transaction through Checkout.com's API.
        
        Args:
            refund_request (RefundRequest)
        Returns:
            Union[RefundResponse, ErrorResponse]: The refund response or error response
        """
        # Set up headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Prepare the refund payload
        payload = {
            "reference": refund_request.reference,
            "amount": refund_request.amount.value,
            "currency": refund_request.amount.currency
        }

        try:
            # Make request to Checkout.com
            response = self.request_client.request(
                url=f"{self.base_url}/payments/{refund_request.original_transaction_id}/refunds",
                method="POST",
                headers=headers,
                data=payload,
                use_bt_proxy=False  # Refunds don't need BT proxy
            )

            response_data = response.json()
            
            # Transform the response to a standardized format
            return RefundResponse(
                id=response_data.get('action_id'),
                reference=response_data.get('reference'),
                amount=Amount(value=response_data.get('amount'), currency=response_data.get('currency')),
                status=TransactionStatus(code=TransactionStatusCode.RECEIVED, provider_code=""),
                full_provider_response=response_data,
                created_at=datetime.now(timezone.utc).isoformat(),
                refunded_transaction_id=refund_request.original_transaction_id
            )

        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
            except:
                error_data = None

            raise TransactionException(self._transform_error_response_object(e.response, error_data))
            
