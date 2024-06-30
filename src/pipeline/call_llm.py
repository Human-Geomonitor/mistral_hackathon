"""Functions related to LLM calls."""

import json
import os
from typing import Optional

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

_client: Optional[MistralClient] = None


def get_mistral_client():
    """Get the Mistral AI client. You need to have your API key in the environment variables under MISTRAL_API_KEY."""
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("MISTRAL_API_KEY")
    client = MistralClient(api_key=api_key)
    return client


def call_mistral_model(client: MistralClient, model_name: str, input_text: str) -> dict:
    """Call a Mistral AI model for prediction.

    Args:
        client (MistralClient): client to connect to the Mistral AI API.
        model_name (str): name of the model to query.
        input_text (str): input text from the model.

    Returns:
        dict: dictionary with relevant information.
    """
    llm_response = client.chat(
        model=model_name, messages=[ChatMessage(role="user", content=input_text)]
    )
    response = llm_response.choices[0].message.content
    json_response = json.loads(response)
    return json_response
