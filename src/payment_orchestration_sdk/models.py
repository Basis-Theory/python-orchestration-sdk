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
    ONE_TIME     = "ONE_TIME"
    CARD_ON_FILE = "CARD_ON_FILE"
    SUBSCRIPTION = "SUBSCRIPTION"
    UNSCHEDULED = "UNSCHEDULED"


class SourceType(str, Enum):
    BASIS_THEORY_TOKEN = "basis_theory_token"
    BASIS_THEORY_TOKEN_INTENT = "basistheory_token_intent"
    PROCESSOR_TOKEN = "processor_token"


class ErrorCategory(str, Enum):
    PROCESSING_ERROR = "Processing Error"
    PAYMENT_METHOD_ERROR = "Payment Method Error"
    FRAUD_DECLINE = "Fraud Decline"
    AUTHENTICATION_ERROR = "Authentication Error"
    OTHER = "Other"


class ErrorType(str, Enum):
    REFUSED = "refused"
    REFERRAL = "referral"
    ACQUIRER_ERROR = "acquirer_error"
    BLOCKED_CARD = "blocked_card"
    EXPIRED_CARD = "expired_card"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_CARD_NUMBER = "invalid_card_number"
    ISSUER_UNAVAILABLE = "issuer_unavailable"
    PAYMENT_NOT_SUPPORTED = "payment_not_supported"
    THREE_DS_ERROR = "3ds_error"
    INSUFFICIENT_FUNDS = "insufficent_funds"
    FRAUD = "fraud"
    PAYMENT_CANCELLED = "payment_cancelled"
    PAYMENT_CANCELLED_BY_CONSUMER = "payment_cancelled_by_consumer"
    PIN_INVALID = "pin_invalid"
    INCORRECT_PAYMENT = "incorrect_payment"
    CVC_INVALID = "cvc_invalid"
    RESTRICTED_CARD = "restricted_card"
    STOP_PAYMENT = "stop_payment"
    OTHER = "other"
    AVS_DECLINE = "avs_declince"
    PIN_REQUIRED = "pin_required"
    BANK_ERROR = "bank_error"
    CONTACTLESS_FALLBACK = "contactless_fallback"
    AUTHENTICATION_REQUIRED = "authentication_required"
    AUTHENTICATION_FAILURE = "authentication_failure"
    PROCESSOR_BLOCKED = "processor_blocked"
    DUPLICATE_PAYMENT = "duplicate_payment"
    CARD_LOST = "card_lost"
    PAYMENT_CAPTURE_INVALID = "payment_capture_invalid"
    CARD_CARDHOLDER_INVALID = "card_cardholder_invalid"
    NETWORK_TRANSACTION_ID_INVALID = "network_transaction_id_invalid"
    PROCESSOR_TOKEN_ERROR = "processor_token_error"


@dataclass
class Amount:
    value: int
    currency: str = "USD"


@dataclass
class Source:
    type: SourceType
    id: str
    store_with_provider: bool = False
    holderName: Optional[str] = None


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
    networkTransactionId: Optional[str] = None 


@dataclass
class ErrorCode:
    category: str
    code: str


@dataclass
class ErrorResponse:
    error_codes: list[ErrorCode]
    provider_errors: list[str]
    full_provider_response: Dict[str, Any] 