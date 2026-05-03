import contextlib
from datetime import datetime
from pathlib import Path
from typing import Literal

import aiofiles
import httpx
from pydantic import BaseModel
from sanic import Sanic
from sanic.log import logger

from app.core.constants import ENCODING
from app.models.media import Language, MediaItem
from app.utils import json

# the display mode of the danmaku
type Mode = Literal["scroll", "top", "bottom"]


class Danmaku(BaseModel):
    # unique id
    id: str | None = None
    # comment text
    text: str
    # display mode
    mode: Mode | None = None
    # color in hex format
    color: str | None = None
    # start time in milliseconds
    start: int | None = None


class DanmakuService:
    """The service class for all danmaku related operations."""

    @classmethod
    def _base_url(cls, server: str) -> str:
        """Get the base URL for the danmaku server API.

        Args:
            server: The danmaku server base URL.

        Returns:
            The base URL for the danmaku server API.
        """
        base_url = server.rstrip("/")
        if base_url.endswith(("/v2", "/api/v2")):
            return base_url
        return f"{base_url}/api/v2"

    @classmethod
    async def match_danmakus(cls, path: str) -> list[Danmaku]:
        """Match danmakus for the given media resource.

        Args:
            path: The media resource path.

        Returns:
            A list of matched danmakus.
        """
        # get the media item by the path
        media = await MediaItem.filter(path=path).first().select_related("lib")
        if not media:
            return []
        danmaku_path = media.danmaku_path

        # default local cache path: {media_dir}/.{media_name}.json
        if not danmaku_path:
            danmaku_path = Path(media.dir) / f".{media.name}.json"

        # check if the local cache file exists
        danmaku_path = Path(danmaku_path)
        cached = danmaku_path.exists()

        # check if the local cache file is expired
        expired = False
        if cached and (ttl := media.lib.danmaku_ttl) is not None:
            mtime = danmaku_path.stat().st_mtime
            if mtime + ttl * 3600 < datetime.now().timestamp():
                expired = True

        if (not cached or expired) and (server := media.lib.danmaku_server):
            danmaku_id = media.danmaku_id
            if not danmaku_id:
                # try to match the episode ID from the danmaku server
                danmaku_id = await cls.match_episode_id(server, media)

            if danmaku_id:
                # load danmakus from the danmaku server
                danmakus = await cls.load_from_server(
                    server, danmaku_id, media.lib.language
                )
                if danmakus:
                    # save to local cache file
                    async with aiofiles.open(danmaku_path, "wb") as f:
                        await f.write(json.dumps([d.model_dump() for d in danmakus]))

                    # update the media item with the danmaku info
                    await MediaItem.filter(id=media.id).update(
                        danmaku_id=danmaku_id,
                        danmaku_path=str(danmaku_path),
                    )

                    return danmakus

        # load danmakus from the local cache file
        return await cls.load_from_cache(danmaku_path)

    @classmethod
    async def match_episode_id(cls, server: str, media: MediaItem) -> str | None:
        """Match the episode ID for the given media item from the danmaku server.

        Args:
            server: The danmaku server base URL.
            media: The media item instance.

        Returns:
            The matched episode ID, or None if not found.
        """
        client: httpx.AsyncClient = Sanic.get_app().ctx.httpx
        try:
            url = f"{cls._base_url(server)}/match"
            response = await client.post(
                url,
                json={
                    "fileName": media.name,
                    "fileHash": media.hash,
                    "fileSize": media.size,
                },
            )
            if response.status_code == 200:
                data = response.json()
                if not data.get("success"):
                    logger.error(
                        'Failed to match episode ID for media "%s": %s',
                        media.name,
                        data.get("errorMessage"),
                    )
                    return None

                matches = data.get("matches")
                if isinstance(matches, list) and matches:
                    episode_id = matches[0].get("episodeId")
                    logger.info(
                        'Matched episode ID "%s" for media "%s" from: %s',
                        episode_id,
                        media.name,
                        server,
                    )
                    return episode_id
        except httpx.RequestError:
            logger.error("An error occurred while requesting %s.", url, exc_info=True)

        return None

    @classmethod
    async def load_from_cache(cls, path: Path) -> list[Danmaku]:
        """Load danmakus from the local cache file.

        Args:
            path: The local cache file path.

        Returns:
            A list of danmakus loaded from the cache.
        """
        if not path.exists():
            return []

        async with aiofiles.open(path, encoding=ENCODING) as f:
            danmakus = json.loads(await f.read())
        return [Danmaku.model_validate(danmaku) for danmaku in danmakus]

    @classmethod
    async def load_from_server(
        cls, server: str, episode_id: str, language: Language | None = None
    ) -> list[Danmaku]:
        """Load danmakus from the danmaku server.

        Args:
            server: The danmaku server base URL.
            episode_id: The episode ID.
            language: The optional language code.

        Returns:
            A list of danmakus loaded from the server.
        """
        client: httpx.AsyncClient = Sanic.get_app().ctx.httpx
        try:
            url = f"{cls._base_url(server)}/comment/{episode_id}?withRelated=true"
            if language == Language.ZH_CN:
                # request the converted simplified Chinese comments
                url += "&chConvert=1"

            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                comments = data.get("comments")
                if isinstance(comments, list) and comments:
                    return cls.format_danmakus(comments)
        except httpx.RequestError:
            logger.error("An error occurred while requesting %s.", url, exc_info=True)

        return []

    @classmethod
    def format_danmakus(cls, raw: list[dict]) -> list[Danmaku]:
        """Format raw danmaku dicts into Danmaku objects.

        Each dict is expected to have:
          - `cid`: the unique danmaku ID.
          - `p`: a comma-separated string with four fields:
              - `parts[0]` — start time in seconds.
              - `parts[1]` — display mode (1=scroll, 4=bottom, 5=top).
              - `parts[2]` — color as a 32-bit integer.
              - `parts[3]` — user ID (numeric string, ignored here).
          - `m`: the comment text.

        Args:
            raw: List of raw danmaku dicts.

        Returns:
            A list of parsed Danmaku objects.
        """
        _MODE_MAP: dict[str, Mode] = {"1": "scroll", "4": "bottom", "5": "top"}

        danmakus: list[Danmaku] = []
        for item in raw:
            text = item.get("m")
            if not isinstance(text, str):
                continue

            cid = item.get("cid")
            parts = str(item.get("p", "")).split(",")

            # parts[0]: start time in seconds, converted to milliseconds
            start: int | None = None
            if len(parts) >= 1:
                with contextlib.suppress(ValueError):
                    start = int(float(parts[0]) * 1000)

            # parts[1]: display mode, mapped to Mode enum
            mode: Mode | None = None
            if len(parts) >= 2:
                mode = _MODE_MAP.get(parts[1])

            # parts[2]: color integer, converted to hex color string
            color: str | None = None
            if len(parts) >= 3:
                with contextlib.suppress(ValueError):
                    c = int(parts[2])
                    r = (c >> 16) & 0xFF
                    g = (c >> 8) & 0xFF
                    b = c & 0xFF
                    color = f"#{r:02X}{g:02X}{b:02X}"

            danmakus.append(
                Danmaku(
                    id=str(cid) if cid else None,
                    text=text,
                    mode=mode,
                    color=color,
                    start=start,
                )
            )

        return danmakus
