import os
from typing import Callable, Optional

import anthropic

from .base import LLMProvider, ProviderError


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = os.getenv("API_KEY", "").strip()
        if not api_key:
            raise ValueError("API_KEY is not set. Add it to your .env file and restart.")
        self.model_name = os.getenv("MODEL", "claude-sonnet-4-6").strip()
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze_document(
        self,
        image_b64: str,
        extracted_text: str,
        prompt: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        message_payload = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        try:
            if on_chunk is None:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=2048,
                    messages=message_payload,
                )
                return response.content[0].text

            full_text = ""
            with self.client.messages.stream(
                model=self.model_name,
                max_tokens=2048,
                messages=message_payload,
            ) as stream:
                for chunk in stream.text_stream:
                    full_text += chunk
                    on_chunk(chunk)
            return full_text

        except anthropic.AuthenticationError:
            raise ProviderError("Invalid API key. Check your API_KEY and try again.")
        except anthropic.RateLimitError:
            raise ProviderError("Anthropic rate limit reached. Wait a moment and try again.")
        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic API error: {e.message}")
