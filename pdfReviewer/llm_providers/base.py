from abc import ABC, abstractmethod
from typing import Callable, Optional


class ProviderError(Exception):
    """Raised by any provider for auth, rate-limit, or API failures."""


class LLMProvider(ABC):

    @abstractmethod
    def analyze_document(
        self,
        image_b64: str,
        extracted_text: str,
        prompt: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Send image and text to the LLM and return the full response.

        Args:
            image_b64: Base64-encoded PNG of the document page.
            extracted_text: Machine-readable text from the document.
            prompt: Instruction prompt.
            on_chunk: Optional callback called with each streamed text chunk.
                      When provided, the provider streams the response.

        Returns:
            Full response text (JSON array string).
        """
