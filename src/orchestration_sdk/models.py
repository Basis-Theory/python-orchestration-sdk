from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict, List
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
    REFUNDED = "Refunded"

class RecurringType(str, Enum):
    ONE_TIME     = "ONE_TIME"
    CARD_ON_FILE = "CARD_ON_FILE"
    SUBSCRIPTION = "SUBSCRIPTION"
    UNSCHEDULED = "UNSCHEDULED"

class RefundReason(str, Enum):
    FRAUD = "FRAUD"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"
    RETURN = "RETURN"
    DUPLICATE = "DUPLICATE"
    OTHER = "OTHER"


class SourceType(str, Enum):
    BASIS_THEORY_TOKEN = "basis_theory_token"
    BASIS_THEORY_TOKEN_INTENT = "basis_theory_token_intent"
    PROCESSOR_TOKEN = "processor_token"


class ErrorCategory(str, Enum):
    AUTHENTICATION_ERROR = "authentication_error"
    PAYMENT_METHOD_ERROR = "payment_method_error"
    PROCESSING_ERROR = "processing_error"
    VALIDATION_ERROR = "validation_error"
    BASIS_THEORY_ERROR = "basis_theory_error"
    FRAUD_DECLINE = "Fraud Decline"
    OTHER = "Other"


class ErrorType(Enum):  
    """Enum for error types."""
    REFUSED = ("refused", ErrorCategory.PROCESSING_ERROR)
    REFERRAL = ("referral", ErrorCategory.PROCESSING_ERROR)
    ACQUIRER_ERROR = ("acquirer_error", ErrorCategory.OTHER)
    BLOCKED_CARD = ("blocked_card", ErrorCategory.PAYMENT_METHOD_ERROR)
    EXPIRED_CARD = ("expired_card", ErrorCategory.PAYMENT_METHOD_ERROR)
    INVALID_AMOUNT = ("invalid_amount", ErrorCategory.OTHER)
    INVALID_CARD = ("invalid_card", ErrorCategory.PAYMENT_METHOD_ERROR)
    INVALID_SOURCE_TOKEN = ("invalid_source_token", ErrorCategory.PAYMENT_METHOD_ERROR)
    OTHER = ("other", ErrorCategory.OTHER)
    NOT_SUPPORTED = ("not_supported", ErrorCategory.PROCESSING_ERROR)
    AUTHENTICATION_FAILURE = ("authentication_failure", ErrorCategory.AUTHENTICATION_ERROR)
    INSUFFICENT_FUNDS = ("insufficient_funds", ErrorCategory.PAYMENT_METHOD_ERROR)
    FRAUD = ("fraud", ErrorCategory.FRAUD_DECLINE)
    PAYMENT_CANCELLED = ("payment_cancelled", ErrorCategory.OTHER)
    PAYMENT_CANCELLED_BY_CONSUMER = ("payment_cancelled_by_consumer", ErrorCategory.PROCESSING_ERROR)
    INVALID_PIN = ("invalid_pin", ErrorCategory.PAYMENT_METHOD_ERROR)
    PIN_TRIES_EXCEEDED = ("pin_tries_exceeded", ErrorCategory.PAYMENT_METHOD_ERROR)
    CVC_INVALID = ("cvc_invalid", ErrorCategory.PAYMENT_METHOD_ERROR)
    RESTRICTED_CARD = ("restricted_card", ErrorCategory.PROCESSING_ERROR)
    STOP_PAYMENT = ("stop_payment", ErrorCategory.PROCESSING_ERROR)
    AVS_DECLINE = ("avs_decline", ErrorCategory.PROCESSING_ERROR)
    PIN_REQUIRED = ("pin_required", ErrorCategory.PROCESSING_ERROR)
    BANK_ERROR = ("bank_error", ErrorCategory.PROCESSING_ERROR)
    CONTACTLESS_FALLBACK = ("contactless_fallback", ErrorCategory.PROCESSING_ERROR)
    AUTHENTICATION_REQUIRED = ("authentication_required", ErrorCategory.PROCESSING_ERROR)
    PROCESSOR_BLOCKED = ("processor_blocked", ErrorCategory.PROCESSING_ERROR)
    INVALID_API_KEY = ("invalid_api_key", ErrorCategory.OTHER)
    UNAUTHORIZED = ("unauthorized", ErrorCategory.OTHER)
    CONFIGURATION_ERROR = ("configuration_error", ErrorCategory.OTHER)
    REFUND_FAILED = ("refund_failed", ErrorCategory.PROCESSING_ERROR)
    REFUND_AMOUNT_EXCEEDS_BALANCE = ("refund_amount_exceeds_balance", ErrorCategory.PROCESSING_ERROR)
    REFUND_DECLINED = ("refund_declined", ErrorCategory.PROCESSING_ERROR)
    BT_UNAUTHENTICATED = ("unauthenticated", ErrorCategory.BASIS_THEORY_ERROR)
    BT_UNAUTHORIZED = ("unauthorized", ErrorCategory.BASIS_THEORY_ERROR)
    BT_REQUEST_ERROR = ("request_error", ErrorCategory.BASIS_THEORY_ERROR)
    BT_UNEXPECTED = ("unexpected", ErrorCategory.BASIS_THEORY_ERROR)

    def __init__(self, code: str, category: ErrorCategory):
        self.code = code
        self.category = category


@dataclass
class Amount:
    value: int
    currency: str = "USD"


@dataclass
class Source:
    type: SourceType
    id: str
    store_with_provider: bool = False
    holder_name: Optional[str] = None


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
    previous_network_transaction_id: Optional[str] = None
    override_provider_properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, str]] = None

@dataclass
class RefundRequest:
    original_transaction_id: str
    reference: str
    amount: Amount
    reason: Optional[RefundReason] = None

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
    network_transaction_id: Optional[str] = None 


@dataclass
class RefundResponse:
    id: str
    reference: str
    amount: Amount
    status: TransactionStatus
    full_provider_response: Dict[str, Any]
    created_at: datetime
    refunded_transaction_id: Optional[str] = None

@dataclass
class ErrorCode:
    category: str
    code: str

@dataclass
class ErrorResponse:
    error_codes: List[ErrorCode]
    provider_errors: List[str]
    full_provider_response: Dict[str, Any]