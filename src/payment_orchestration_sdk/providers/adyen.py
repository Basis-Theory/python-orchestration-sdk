from typing import Dict, Any
import requests
from ..exceptions import ConfigurationError, APIError, ValidationError
from ..utils import RequestClient, create_transaction_request
from ..models import (
    TransactionRequest,
    Source,
    SourceType,
    RecurringType
)


RECURRING_TYPE_MAPPING = {
    RecurringType.ECOMMERCE: "ecommerce",
    RecurringType.CARD_ON_FILE: "card_on_file",
    RecurringType.SUBSCRIPTION: "subscription",
    RecurringType.UNSCHEDULED: "unscheduled"
}


class AdyenClient:
    def __init__(self, api_key: str, merchant_account: str, is_test: bool, bt_api_key: str):
        self.api_key = api_key
        self.merchant_account = merchant_account
        self.base_url = "https://checkout-test.adyen.com/v70" if is_test else "https://checkout-live.adyen.com/v70"
        self.request_client = RequestClient(bt_api_key)

    def _validate_required_fields(self, data: Dict[str, Any]) -> None:
        if 'amount' not in data or 'value' not in data['amount']:
            raise ValidationError("amount.value is required")
        if 'source' not in data or 'type' not in data['source'] or 'id' not in data['source']:
            raise ValidationError("source.type and source.id are required")

    async def _transform_to_adyen_payload(self, request: TransactionRequest) -> Dict[str, Any]:
        """Transform SDK request to Adyen payload format."""
        payload = {
            "amount": {
                "value": request.amount.value,
                "currency": request.amount.currency
            },
            "merchantAccount": self.merchant_account,
            "shopperInteraction": "ContAuth" if request.merchant_initiated else "Ecommerce",
            "storePaymentMethod": request.source.store_with_provider,
        }

        # Add reference if provided
        if request.reference:
            payload["reference"] = request.reference

        # Add recurring type if provided
        if request.type:
            payload["recurringProcessingModel"] = RECURRING_TYPE_MAPPING[request.type]

        # Process source based on type
        if request.source.type == SourceType.PROCESSOR_TOKEN:
            payload["paymentMethod"] = {
                "type": "scheme",
                "storedPaymentMethodId": request.source.id
            }
        elif request.source.type in [SourceType.BASIS_THEORY_TOKEN, SourceType.BASIS_THEORY_TOKEN_INTENT]:
            # Add card data with Basis Theory expressions
            token_prefix = "token_intent" if request.source.type == SourceType.BASIS_THEORY_TOKEN_INTENT else "token"
            payload["paymentMethod"] = {
                "type": "scheme",
                "number": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.number'}}}}",
                "expiryMonth": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.expiration_month'}}}}",
                "expiryYear": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.expiration_year'}}}}",
                "cvc": f"{{{{ {token_prefix}: {request.source.id} | json: '$.data.cvc'}}}}"
            }

        # Add customer information
        if request.customer:
            if request.customer.reference:
                payload["shopperReference"] = request.customer.reference

            # Map name fields
            if request.customer.first_name or request.customer.last_name:
                payload["shopperName"] = {}
                if request.customer.first_name:
                    payload["shopperName"]["firstName"] = request.customer.first_name
                if request.customer.last_name:
                    payload["shopperName"]["lastName"] = request.customer.last_name

            # Map email directly
            if request.customer.email:
                payload["shopperEmail"] = request.customer.email

            # Map address fields
            if request.customer.address:
                address = request.customer.address
                if any([address.address_line1, address.city, address.state, address.zip, address.country]):
                    payload["billingAddress"] = {}

                    # Map address_line1 to street
                    if address.address_line1:
                        payload["billingAddress"]["street"] = address.address_line1

                    # address_line2 is not mapped as per CSV

                    if address.city:
                        payload["billingAddress"]["city"] = address.city

                    if address.state:
                        payload["billingAddress"]["stateOrProvince"] = address.state

                    if address.zip:
                        payload["billingAddress"]["postalCode"] = address.zip

                    # Set country to ZZ if address exists but no country specified
                    payload["billingAddress"]["country"] = address.country or "ZZ"

        # Map statement description (only name, city is not mapped as per CSV)
        if request.statement_description and request.statement_description.name:
            payload["shopperStatement"] = request.statement_description.name

        # Map 3DS information
        if request.three_ds:
            payload["additionalData"] = {"threeDSecure": {}}

            if request.three_ds.eci:
                payload["additionalData"]["threeDSecure"]["eci"] = request.three_ds.eci

            if request.three_ds.authentication_value:
                payload["additionalData"]["threeDSecure"]["authenticationValue"] = request.three_ds.authentication_value

            if request.three_ds.xid:
                payload["additionalData"]["threeDSecure"]["xid"] = request.three_ds.xid

            if request.three_ds.version:
                payload["additionalData"]["threeDSecure"]["threeDSVersion"] = request.three_ds.version

        return payload

    async def transaction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment transaction through Adyen's API directly or via Basis Theory's proxy."""
        try:
            self._validate_required_fields(request_data)

            # Convert the dictionary to our internal TransactionRequest model
            request = create_transaction_request(request_data)

            # Transform to Adyen's format
            payload = await self._transform_to_adyen_payload(request)

            # Set up common headers
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }

            # Make the request (using proxy for BT tokens, direct for processor tokens)
            response = self.request_client.request(
                url=f"{self.base_url}/payments",
                method="POST",
                headers=headers,
                data=payload,
                use_bt_proxy=request.source.type != SourceType.PROCESSOR_TOKEN
            )

            print(response.json())
            response.raise_for_status()
            return response.json()

        except KeyError as e:
            raise ValidationError(f"Missing required field: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {str(e)}")
