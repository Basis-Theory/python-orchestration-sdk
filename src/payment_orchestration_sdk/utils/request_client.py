from typing import Dict, Any
import requests


class RequestClient:
    def __init__(self, bt_api_key: str, bt_proxy_url: str = "https://api.basistheory.com/proxy"):
        self.bt_api_key = bt_api_key
        self.bt_proxy_url = bt_proxy_url

    def request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        data: Dict[str, Any],
        use_bt_proxy: bool = False,
    ) -> requests.Response:
        """
        Make an HTTP request, optionally through the Basis Theory proxy.
        
        Args:
            url: The destination URL
            method: HTTP method (POST, GET, etc.)
            headers: Headers to include in the request
            data: Request payload
            use_bt_proxy: Whether to route through BT proxy
            
        Returns:
            requests.Response: The HTTP response
        """
        if use_bt_proxy:
            # Add BT-specific headers
            headers = {
                **headers,
                "BT-API-KEY": self.bt_api_key,
                "BT-PROXY-URL": url,
            }
            request_url = self.bt_proxy_url
        else:
            request_url = url

        return requests.request(
            method=method,
            url=request_url,
            json=data,
            headers=headers
        ) 