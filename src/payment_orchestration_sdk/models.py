from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict
from datetime import datetime


class TransactionStatusCode(str, Enum):
    AUTHORIZED = "Authorized"
    PENDING = "Pending"
    CARD_VERIFIED = "Card Verified"
    DECLINED = "Declined"
    RETRY_SCHEDULED = "Retry Scheduled"
    CANCELLED = "Cancelled"
    CHALLENGE_SHOPPER = "ChallengeShopper"
    RECEIVED = "Received"
    PARTIALLY_AUTHORIZED = "PartiallyAuthorised"


class RecurringType(str, Enum):
    ECOMMERCE = "ECOMMERCE"
    CARD_ON_FILE = "CARD_ON_FILE"
    SUBSCRIPTION = "SUBSCRIPTION"
    UNSCHEDULED = "UNSCHEDULED"


class SourceType(str, Enum):
    BASIS_THEORY_TOKEN = "basis_theory_token"
    BASIS_THEORY_TOKEN_INTENT = "basistheory_token_intent"
    PROCESSOR_TOKEN = "processor_token"


@dataclass
class Amount:
    value: int
    currency: str = "USD"


@dataclass
class Source:
    type: SourceType
    id: str
    store_with_provider: bool = False


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
    reference: Optional[str] = None
    merchant_initiated: bool = False
    type: Optional[RecurringType] = None
    customer: Optional[Customer] = None
    statement_description: Optional[StatementDescription] = None
    three_ds: Optional[ThreeDS] = None


# Response Models
@dataclass
class TransactionStatus:
    code: TransactionStatusCode
    provider_code: str


@dataclass
class TransactionThreeDS:
    downgraded: bool
    enrolled: Optional[str] = None
    eci: Optional[str] = None


@dataclass
class ProvisionedSource:
    id: str


@dataclass
class TransactionSource:
    type: str
    id: str
    provisioned: Optional[ProvisionedSource] = None


@dataclass
class TransactionResponse:
    id: str
    reference: str
    amount: Amount
    status: TransactionStatus
    source: TransactionSource
    full_provider_response: Dict[str, Any]
    created_at: datetime
    three_ds: Optional[TransactionThreeDS] = None 