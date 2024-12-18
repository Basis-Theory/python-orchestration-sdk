from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, Literal

import requests
from ..exceptions import ConfigurationError, APIError, ValidationError


class RecurringType(str, Enum):
    CARD_ON_FILE = "card_on_file"
    SUBSCRIPTION = "subscription"
    UNSCHEDULED = "unscheduled"


class SourceType(str, Enum):
    BASIS_THEORY_TOKEN = "basis_theory_token"
    BASIS_THEORY_TOKEN_INTENT = "basistheory_token_intent"
    PROCESSOR_TOKEN = "processor_token"


@dataclass
class Amount:
    value: int  # Required
    currency: str = "USD"  # Optional with default USD


@dataclass
class Source:
    type: SourceType  # Required
    id: str  # Required
    store_with_provider: bool = False  # Optional with default False


@dataclass
class Address:
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None


@dataclass
class Customer:
    reference: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Address] = None


@dataclass
class StatementDescription:
    name: Optional[str] = None
    city: Optional[str] = None


@dataclass
class ThreeDS:
    eci: Optional[str] = None
    authentication_value: Optional[str] = None
    xid: Optional[str] = None
    version: Optional[str] = None


@dataclass
class TransactionRequest:
    amount: Amount
    source: Source
    merchant_initiated: bool = False
    type: Optional[RecurringType] = None
    customer: Optional[Customer] = None
    statement_description: Optional[StatementDescription] = None
    three_ds: Optional[ThreeDS] = None

class AdyenClient:
    def __init__(self, api_key: str, merchant_account: str, is_test: bool):
        self.api_key = api_key
        self.merchant_account = merchant_account
        self.base_url = "https://checkout-test.adyen.com/v70" if is_test else "https://checkout-live.adyen.com/v70"

    def _validate_required_fields(self, data: Dict[str, Any]) -> None:
        """Validate required fields based on documentation."""
        if 'amount' not in data or 'value' not in data['amount']:
            raise ValidationError("amount.value is required")
        if 'source' not in data or 'type' not in data['source'] or 'id' not in data['source']:
            raise ValidationError("source.type and source.id are required")

    def _transform_address(self, address: Address) -> Dict[str, Any]:
        """Transform address to Adyen format, excluding None values."""
        address_dict = {
            "street": address.address_line1,
            "houseNumberOrName": address.address_line2,
            "city": address.city,
            "stateOrProvince": address.state,
            "postalCode": address.zip,
            "country": address.country
        }
        return {k: v for k, v in address_dict.items() if v is not None}

    def _transform_to_adyen_payload(self, request: TransactionRequest) -> Dict[str, Any]:
        payload = {
            "amount": {
                "value": request.amount.value,
                "currency": request.amount.currency
            },
            "merchantAccount": self.merchant_account,
            "shopperInteraction": "ContAuth" if request.merchant_initiated else "Ecommerce",
            "storePaymentMethod": request.source.store_with_provider,
        }

        # Add recurring type if specified
        if request.type:
            payload["recurringProcessingModel"] = request.type.value

        # Add source information
        if request.source.type == SourceType.BASIS_THEORY_TOKEN:
            payload["paymentMethod"] = {"type": "scheme", "basisTheoryToken": request.source.id}
        elif request.source.type == SourceType.BASIS_THEORY_TOKEN_INTENT:
            payload["paymentMethod"] = {"type": "scheme", "basisTheoryTokenIntent": request.source.id}
        elif request.source.type == SourceType.PROCESSOR_TOKEN:
            payload["paymentMethod"] = {"type": "scheme", "processorToken": request.source.id}

        # Add customer information if provided
        if request.customer:
            if request.customer.reference:
                payload["shopperReference"] = request.customer.reference
            if request.customer.first_name or request.customer.last_name:
                payload["shopperName"] = {
                    "firstName": request.customer.first_name,
                    "lastName": request.customer.last_name
                }
            if request.customer.email:
                payload["shopperEmail"] = request.customer.email
            if request.customer.address:
                address_dict = self._transform_address(request.customer.address)
                if address_dict:
                    payload["billingAddress"] = address_dict

        # Add statement description if provided
        if request.statement_description and (request.statement_description.name or request.statement_description.city):
            payload["merchantOrderReference"] = (
                f"{request.statement_description.name or ''} "
                f"{request.statement_description.city or ''}"
            ).strip()

        # Add 3DS information if provided
        if request.three_ds:
            if any([request.three_ds.eci, request.three_ds.authentication_value, request.three_ds.xid]):
                payload["mpiData"] = {
                    k: v for k, v in {
                        "cavv": request.three_ds.authentication_value,
                        "eci": request.three_ds.eci,
                        "xid": request.three_ds.xid,
                    }.items() if v is not None
                }
            if request.three_ds.version:
                payload["threeDSVersion"] = request.three_ds.version

        return payload

    def transaction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment transaction through Adyen's API.

        Args:
            request_data: Transaction request data following the SDK's format

        Returns:
            Dict[str, Any]: Adyen's API response

        Raises:
            ValidationError: If required fields are missing
            ConfigurationError: If configuration is invalid
            APIError: If the API request fails
        """
        try:
            # Validate required fields
            self._validate_required_fields(request_data)

            # Convert the dictionary to our internal TransactionRequest model
            request = TransactionRequest(
                amount=Amount(
                    value=request_data['amount']['value'],
                    currency=request_data['amount'].get('currency', 'USD')
                ),
                source=Source(
                    type=SourceType(request_data['source']['type']),
                    id=request_data['source']['id'],
                    store_with_provider=request_data['source'].get('store_with_provider', False)
                ),
                merchant_initiated=request_data.get('merchant_initiated', False),
                type=RecurringType(request_data['type']) if 'type' in request_data else None,
                customer=Customer(
                    reference=request_data.get('customer', {}).get('reference'),
                    first_name=request_data.get('customer', {}).get('first_name'),
                    last_name=request_data.get('customer', {}).get('last_name'),
                    email=request_data.get('customer', {}).get('email'),
                    address=Address(**request_data['customer']['address'])
                    if 'customer' in request_data and 'address' in request_data['customer']
                    else None
                ) if 'customer' in request_data else None,
                statement_description=StatementDescription(
                    **request_data['statement_description']
                ) if 'statement_description' in request_data else None,
                three_ds=ThreeDS(
                    **{k.lower(): v for k, v in request_data['3ds'].items()}
                ) if '3ds' in request_data else None
            )

            # Transform to Adyen's format
            payload = self._transform_to_adyen_payload(request)

            # Make the API request
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                }
            )

            response.raise_for_status()
            return response.json()

        except KeyError as e:
            raise ValidationError(f"Missing required field: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Adyen API request failed: {str(e)}")
