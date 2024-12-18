class PaymentOrchestrationError(Exception):
    """Base exception for PaymentOrchestrationSDK"""
    pass

class UninitializedError(PaymentOrchestrationError):
    """Raised when SDK is used before initialization"""
    pass

class ValidationError(PaymentOrchestrationError):
    """Raised when request validation fails"""
    pass

class ConfigurationError(PaymentOrchestrationError):
    """Raised when SDK is configured incorrectly"""
    pass

class APIError(PaymentOrchestrationError):
    """Raised when API request fails"""
    pass