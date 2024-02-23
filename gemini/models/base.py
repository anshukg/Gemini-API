# Refer to https://github.com/HanaokaYuzu/Gemini-API/
import re
from datetime import datetime
from typing import List, Dict
from loguru import logger
from httpx import AsyncClient, HTTPError
from pydantic import BaseModel, root_validator


class Image(BaseModel):
    """Single image object from Gemini."""

    url: str
    title: str = "[Image]"
    alt: str = ""

    def __str__(self) -> str:
        return f"{self.title}({self.url}) - {self.alt}"

    def __repr__(self) -> str:
        return f"Image(title='{self.title}', url='{self._truncated_url()}', alt='{self.alt}')"

    def _truncated_url(self) -> str:
        return (
            self.url if len(self.url) <= 20 else self.url[:8] + "..." + self.url[-12:]
        )

    def save(
        self, path: str = "temp/", filename: str = None, cookies: Dict[str, str] = None
    ) -> None:
        """Save the image to disk."""
        filename = filename or re.search(r"^(.*\.\w+)", self.url.split("/")[-1]).group()

        with AsyncClient(follow_redirects=True, cookies=cookies) as client:
            response = client.get(self.url)
            response.raise_for_status()  # Raise an exception for non-200 responses
            content_type = response.headers.get("content-type")
            if content_type and "image" not in content_type:
                logger.warning(
                    f"Content type of {filename} is not image, but {content_type}."
                )
            with open(f"{path}{filename}", "wb") as file:
                file.write(response.read())


class WebImage(Image):
    """Image from the web."""

    pass


class GeneratedImage(Image):
    """Image generated by ImageFX."""

    cookies: Dict[str, str]

    @root_validator
    def validate_cookies(cls, values: Dict[str, str]) -> Dict[str, str]:
        if "__Secure-1PSID" not in values or "__Secure-1PSIDTS" not in values:
            raise ValueError(
                "Cookies must contain '__Secure-1PSID' and '__Secure-1PSIDTS'"
            )
        return values

    def save(self, path: str = "temp/", filename: str = None) -> None:
        """Save the image to disk."""
        filename = (
            filename
            or f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.url[-10:]}.png"
        )
        super().save(path, filename, self.cookies)


class Candidate(BaseModel):
    """A reply candidate object."""

    rcid: str
    text: str
    web_images: List[WebImage] = []
    generated_images: List[GeneratedImage] = []

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"Candidate(rcid='{self.rcid}', text='{self._truncated_text()}', images={self.images})"

    def _truncated_text(self) -> str:
        return self.text if len(self.text) <= 20 else self.text[:20] + "..."

    @property
    def images(self) -> List[Image]:
        return self.web_images + self.generated_images


class GeminiOutput(BaseModel):
    """Classified output from gemini.google.com."""

    metadata: List[str]
    candidates: List[Candidate]
    chosen: int = 0

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"GeminiOutput(metadata={self.metadata}, chosen={self.chosen}, candidates={self.candidates})"

    @property
    def text(self) -> str:
        return self.candidates[self.chosen].text

    @property
    def images(self) -> List[Image]:
        return self.candidates[self.chosen].images

    @property
    def rcid(self) -> str:
        return self.candidates[self.chosen].rcid
