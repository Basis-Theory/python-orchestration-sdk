from orchestration_sdk.models import ErrorResponse

class TransactionException(Exception):
    error_response: ErrorResponse
    def __init__(self, error_response: 'ErrorResponse'):
        self.error_response = error_response
        super().__init__(str(error_response.error_codes))

class ValidationError(Exception):
    """Raised when request validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when SDK configuration is invalid."""
    pass

class BasisTheoryError(Exception):
    """Raised when Basis Theory returns an error."""
    error_response: ErrorResponse
    def __init__(self, error_response: 'ErrorResponse'):
        self.error_response = error_response
        super().__init__(str(error_response.error_codes))