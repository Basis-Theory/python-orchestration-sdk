from typing import Dict, Any, Optional
import requests
from ..models import ErrorType


class RequestClient:
    def __init__(self, bt_api_key: str):
        self.bt_api_key = bt_api_key

    def _is_bt_error(self, response: requests.Response) -> bool:
        """Check if the error is from BasisTheory by comparing status codes."""
        bt_status = response.headers.get('BT-PROXY-DESTINATION-STATUS')
        return bt_status is None or str(response.status_code) != bt_status

    def _transform_bt_error(self, response: requests.Response) -> Dict[str, Any]:
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

        return {
            "error_codes": [
                {
                    "category": error_type.category,
                    "code": error_type.code
                }
            ],
            "provider_errors": [
                {"error": key, "details": value} 
                for key, value in response_data.get("proxy_error", {}).get("errors", {}).items()
            ],
            "full_provider_response": response_data
        }

    def request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_bt_proxy: bool = False
    ) -> requests.Response:
        """Make an HTTP request, optionally through the BasisTheory proxy."""
        if headers is None:
            headers = {}

        if use_bt_proxy:
            # Add BT API key and proxy headers
            headers["BT-API-KEY"] = self.bt_api_key
            # Add proxy header only if not already present
            if "BT-PROXY-URL" not in headers:
                headers["BT-PROXY-URL"] = url
            # Use the BT proxy endpoint
            request_url = "https://api.basistheory.com/proxy"
        else:
            request_url = url

        # Make the request
        response = requests.request(
            method=method,
            url=request_url,
            headers=headers,
            json=data
        )

        print(f"is_bt_error: {self._is_bt_error(response)}")
        # Check for BT errors first
        if not response.ok and self._is_bt_error(response):
            error_response = self._transform_bt_error(response)
            # Raise an HTTPError with the transformed error response
            error = requests.exceptions.HTTPError(response=response)
            error.bt_error_response = error_response
            raise error

        # Raise for other HTTP errors
        response.raise_for_status()
        
        return response 