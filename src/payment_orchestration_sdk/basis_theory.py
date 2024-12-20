from typing import Dict, Any, Optional
import basistheory
from basistheory.api import tokens_api


class BasisTheoryClient:
    def __init__(self, api_key: str):
        bt_client = basistheory.ApiClient(basistheory.Configuration(
            api_key = api_key
        ))
        self.token_client = tokens_api.TokensApi(bt_client)

    async def process_token(self, token_id: str) -> Dict[str, Any]:
        """
        Process a Basis Theory token and return payment method data.
        This is a placeholder function that will be implemented later.

        Args:
            token_id: The Basis Theory token ID to process

        Returns:
            Dict containing the processed payment method data
        """
        retrieved_token = self.token_client.get_by_id(id=token_id)

        return {
            "type": "scheme",
            "number": retrieved_token['data']['number'],
            "expiryMonth": retrieved_token['data']['expiration_month'],
            "expiryYear": retrieved_token['data']['expiration_year'],
            "cvc": retrieved_token['data']['cvc'],
        }


    async def process_token_intent(self, token_intent_id: str) -> Dict[str, Any]:
        """
        Process a Basis Theory token intent and return payment method data.
        This is a placeholder function that will be implemented later.

        Args:
            token_intent_id: The Basis Theory token intent ID to process

        Returns:
            Dict containing the processed payment method data
        """
        # This will be implemented later
        pass
