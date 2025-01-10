class PaymentOrchestrationError(Exception):
    """Base exception for PaymentOrchestrationSDK"""
    pass

class UninitializedError(PaymentOrchestrationError):
    """Raised when SDK is used before initialization"""
    pass

class ValidationError(Exception):
    """Raised when request validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when SDK configuration is invalid."""
    pass

class APIError(Exception):
    """Raised when an API request fails."""
    pass

class ProcessingError(Exception):
    """Raised when transaction processing fails."""
    pass
