from typing import Dict, Any, Optional, Union, List, cast
import requests
from requests.models import Response
from ..models import ErrorType


class RequestClient:
    def __init__(self, bt_api_key: str) -> None:
        self.bt_api_key = bt_api_key

    def _is_bt_error(self, response: Response) -> bool:
        """Check if the error is from BasisTheory by comparing status codes."""
        bt_status = response.headers.get('BT-PROXY-DESTINATION-STATUS')
        return bt_status is None or str(response.status_code) != bt_status

    def _transform_bt_error(self, response: Response) -> Dict[str, Any]:
        """Transform BasisTheory error response to standardized format."""
        error_type = ErrorType.BT_UNEXPECTED  # Default error type
        
        if response.status_code == 401:
            error_type = ErrorType.BT_UNAUTHENTICATED
        elif response.status_code == 403:
            error_type = ErrorType.BT_UNAUTHORIZED
        elif response.status_code < 500:
            error_type = ErrorType.BT_REQUEST_ERROR

        try:
            response_data = response.json()
        except:
            response_data = {"message": response.text or "Unknown error"}

        provider_errors: List[Dict[str, str]] = []
        proxy_error = response_data.get("proxy_error", {})
        errors = proxy_error.get("errors", {}) if isinstance(proxy_error, dict) else {}
        
        for key, value in errors.items():
            if isinstance(key, str):
                provider_errors.append({
                    "error": key,
                    "details": str(value)
                })

        return {
            "error_codes": [
                {
                    "category": error_type.category,
                    "code": error_type.code
                }
            ],
            "provider_errors": provider_errors,
            "full_provider_response": response_data
        }

    def request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_bt_proxy: bool = False
    ) -> Response:
        """Make an HTTP request, optionally through the BasisTheory proxy."""
        request_headers = headers.copy() if headers else {}

        if use_bt_proxy:
            # Add BT API key and proxy headers
            request_headers["BT-API-KEY"] = self.bt_api_key
            # Add proxy header only if not already present
            if "BT-PROXY-URL" not in request_headers:
                request_headers["BT-PROXY-URL"] = url
            # Use the BT proxy endpoint
            request_url = "https://api.basistheory.com/proxy"
        else:
            request_url = url

        # Make the request
        response = requests.request(
            method=method,
            url=request_url,
            headers=request_headers,
            json=data
        )

        # Check for BT errors first
        if use_bt_proxy and not response.ok and self._is_bt_error(response):
            error_response = self._transform_bt_error(response)
 
            raise BasisTheoryError(error_response)

        # Raise for other HTTP errors
        response.raise_for_status()
        
        return response 