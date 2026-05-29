import base64
import os
from typing import Callable, Optional

from google import genai
from google.genai import types

from .base import LLMProvider, ProviderError


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = os.getenv("API_KEY", "").strip()
        if not api_key:
            raise ValueError("API_KEY is not set. Add it to your .env file and restart.")
        self.model_name = os.getenv("MODEL", "gemini-2.5-flash").strip()
        self.client = genai.Client(api_key=api_key)

    def analyze_document(
        self,
        image_b64: str,
        extracted_text: str,
        prompt: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        image_bytes = base64.b64decode(image_b64)
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            types.Part.from_text(text=prompt),
        ]
        try:
            if on_chunk is None:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                )
                return response.text

            full_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
            ):
                delta = chunk.text or ""
                if delta:
                    full_text += delta
                    on_chunk(delta)
            return full_text

        except Exception as e:
            msg = str(e).lower()
            if any(k in msg for k in ("api_key", "authentication", "permission")):
                raise ProviderError("Invalid API key. Check your API_KEY and try again.")
            if any(k in msg for k in ("quota", "rate")):
                raise ProviderError("Gemini rate limit reached. Wait a moment and try again.")
            raise ProviderError(f"Gemini API error: {e}")
