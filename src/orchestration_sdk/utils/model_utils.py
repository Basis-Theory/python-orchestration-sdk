from typing import Dict, Any, Optional
from ..models import (
    TransactionRequest,
    Amount,
    Source,
    SourceType,
    Customer,
    Address,
    StatementDescription,
    ThreeDS,
    RecurringType
)
from ..exceptions import ValidationError


def validate_required_fields(data: TransactionRequest) -> None:
    """
    Validate required fields in a transaction request.
    
    Args:
        data: TransactionRequest containing transaction request data
        
    Raises:
        ValidationError: If required fields are missing
    """
    if not data.amount or not data.amount.value:
        raise ValidationError("amount.value is required")
    if not data.source or not data.source.type or not data.source.id:
        raise ValidationError("source.type and source.id are required")


def create_transaction_request(data: Dict[str, Any]) -> TransactionRequest:
    """
    Convert a dictionary into a TransactionRequest model.
    
    Args:
        data: Dictionary containing transaction request data
        
    Returns:
        TransactionRequest: A fully populated TransactionRequest object
        
    Raises:
        ValidationError: If required fields are missing
    """
    return TransactionRequest(
        amount=Amount(
            value=data.get('amount', {}).get('value', 0),
            currency=data.get('amount', {}).get('currency', 'USD')
        ),
        source=Source(
            type=SourceType(data.get('source', {}).get('type', '')),
            id=data.get('source', {}).get('id', ''),
            store_with_provider=data.get('source', {}).get('store_with_provider', False),
            holder_name=data.get('source', {}).get('holder_name', '')
        ),
        reference=data.get('reference'),
        merchant_initiated=data.get('merchant_initiated', False),
        type=RecurringType(data.get('type', '')) if 'type' in data else None,
        customer=_create_customer(data.get('customer')) if 'customer' in data else None,
        statement_description=StatementDescription(**data.get('statement_description', {}))
        if 'statement_description' in data else None,
        three_ds=_create_three_ds(data.get('3ds')) if '3ds' in data else None,
        override_provider_properties=data.get('override_provider_properties')
    )


def _create_customer(data: Optional[Dict[str, Any]]) -> Optional[Customer]:
    """Create a Customer model from dictionary data."""
    if not data:
        return None
        
    return Customer(
        reference=data.get('reference'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data.get('email'),
        address=_create_address(data.get('address'))
    )


def _create_address(data: Optional[Dict[str, Any]]) -> Optional[Address]:
    """Create an Address model from dictionary data."""
    if not data:
        return None
        
    return Address(**data)


def _create_three_ds(data: Optional[Dict[str, Any]]) -> Optional[ThreeDS]:
    """Create a ThreeDS model from dictionary data."""
    if not data:
        return None
        
    return ThreeDS(**{k.lower(): v for k, v in data.items()}) 