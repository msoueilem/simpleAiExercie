import os
from typing import Callable, Optional

from openai import OpenAI, AuthenticationError, RateLimitError, APIError

from .base import LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = os.getenv("API_KEY", "").strip()
        if not api_key:
            raise ValueError("API_KEY is not set. Add it to your .env file and restart.")
        self.model_name = os.getenv("MODEL", "gpt-4o").strip()
        self.client = OpenAI(api_key=api_key)

    def analyze_document(
        self,
        image_b64: str,
        extracted_text: str,
        prompt: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ]
        try:
            if on_chunk is None:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    max_tokens=2048,
                    messages=messages,
                )
                return response.choices[0].message.content

            full_text = ""
            for chunk in self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=2048,
                messages=messages,
                stream=True,
            ):
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_text += delta
                    on_chunk(delta)
            return full_text

        except AuthenticationError:
            raise ProviderError("Invalid API key. Check your API_KEY and try again.")
        except RateLimitError:
            raise ProviderError("OpenAI rate limit reached. Wait a moment and try again.")
        except APIError as e:
            raise ProviderError(f"OpenAI API error: {e.message}")
