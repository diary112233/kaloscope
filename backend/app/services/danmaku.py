from typing import Literal

from pydantic import BaseModel


class Danmaku(BaseModel):
    id: str | None = None
    text: str
    mode: Literal["scroll", "top", "bottom"] | None = None
    color: str | None = None
    start: int | None = None


class DanmakuService:
    """The service class for all danmaku related operations."""

    @classmethod
    async def match_danmakus(cls, path: str) -> list[Danmaku]:
        """Match danmakus for the given media resource.

        Args:
            path: The media resource path.

        Returns:
            A list of matched danmakus.
        """
        return []
