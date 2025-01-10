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
            value=data['amount']['value'],
            currency=data['amount'].get('currency', 'USD')
        ),
        source=Source(
            type=SourceType(data['source']['type']),
            id=data['source']['id'],
            store_with_provider=data['source'].get('store_with_provider', False),
            holderName=data['source'].get('holderName')
        ),
        reference=data.get('reference'),
        merchant_initiated=data.get('merchant_initiated', False),
        type=RecurringType(data['type']) if 'type' in data else None,
        customer=_create_customer(data.get('customer')) if 'customer' in data else None,
        statement_description=StatementDescription(**data['statement_description'])
        if 'statement_description' in data else None,
        three_ds=_create_three_ds(data.get('3ds')) if '3ds' in data else None
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