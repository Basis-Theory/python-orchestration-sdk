from typing import Dict, Any, Optional


class BasisTheoryClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def process_token(self, token_id: str) -> Dict[str, Any]:
        """
        Process a Basis Theory token and return payment method data.
        This is a placeholder function that will be implemented later.

        Args:
            token_id: The Basis Theory token ID to process

        Returns:
            Dict containing the processed payment method data
        """
        # This will be implemented later
        pass

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
