import contextlib
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import quote

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
    """The data model for a single danmaku."""

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


class DanmakuMeta(BaseModel):
    """The metadata for a danmaku collection."""

    anime_id: int
    anime_title: str | None = None
    episode_id: int
    episode_title: str | None = None
    type: str
    type_description: str | None = None


class DanmakuWrapper(BaseModel):
    """The wrapper for danmakus with additional metadata."""

    metadata: DanmakuMeta | None = None
    comments: list[Danmaku]


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
    def _append_query(cls, url: str, query: str) -> str:
        """Append query parameters to a URL.

        Args:
            url: The URL to append to.
            query: The query string to append.

        Returns:
            The URL with the query string appended.
        """
        if not query.startswith("?"):
            query = "?" + query
        if "?" in url:
            # proxy mode: append the query as a URL-encoded parameter
            return f"{url}{quote(query)}"
        return f"{url}{query}"

    @classmethod
    async def match_danmakus(cls, path: str) -> DanmakuWrapper:
        """Match danmakus for the given media resource.

        Args:
            path: The media resource path.

        Returns:
            The wrapped danmakus with metadata if available.
        """
        # get the media item by the path
        media = await MediaItem.filter(path=path).first().select_related("lib")
        if not media:
            return DanmakuWrapper(comments=[])
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
            meta = media.danmaku_meta
            if not meta:
                # try to match the metadata from the danmaku server
                meta = await cls.match_metadata(server, media)

            if meta:
                # load danmakus from the danmaku server
                meta = DanmakuMeta.model_validate(meta)
                danmakus = await cls.load_from_server(
                    server, str(meta.episode_id), media.lib.language
                )
                if danmakus:
                    # save to local cache file
                    async with aiofiles.open(danmaku_path, "wb") as f:
                        await f.write(json.dumps([d.model_dump() for d in danmakus]))

                    # update the media item with the danmaku info
                    await MediaItem.filter(id=media.id).update(
                        danmaku_meta=meta,
                        danmaku_path=str(danmaku_path),
                    )

                    return DanmakuWrapper(metadata=meta, comments=danmakus)

        # load danmakus from the local cache file
        meta = media.danmaku_meta
        return DanmakuWrapper(
            metadata=DanmakuMeta.model_validate(meta) if meta else None,
            comments=await cls.load_from_cache(danmaku_path),
        )

    @classmethod
    async def match_metadata(cls, server: str, media: MediaItem) -> DanmakuMeta | None:
        """Match the metadata for the given media item from the danmaku server.

        Args:
            server: The danmaku server base URL.
            media: The media item instance.

        Returns:
            The matched metadata, or None if not found.
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
            if response.status_code != 200:
                logger.error(
                    'Failed to match metadata for media "%s": HTTP %s',
                    media.name,
                    response.status_code,
                )
                return None

            data = response.json()
            if not data.get("success"):
                logger.error(
                    'Failed to match metadata for media "%s": %s',
                    media.name,
                    data.get("errorMessage"),
                )
                return None

            matches = data.get("matches")
            if (
                matches
                and isinstance(matches, list)
                and isinstance((m := matches[0]), dict)
            ):
                meta = DanmakuMeta(
                    anime_id=m.get("animeId", 0),
                    anime_title=m.get("animeTitle"),
                    episode_id=m.get("episodeId", 0),
                    episode_title=m.get("episodeTitle"),
                    type=m.get("type", ""),
                    type_description=m.get("typeDescription"),
                )
                logger.info(
                    'Matched episode ID "%s" for media "%s" from: %s',
                    meta.episode_id,
                    media.name,
                    server,
                )
                return meta
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
            url = f"{cls._base_url(server)}/comment/{episode_id}"
            query = "withRelated=true"
            if language == Language.ZH_CN:
                # request the converted simplified Chinese comments
                query += "&chConvert=1"

            response = await client.get(cls._append_query(url, query))
            if response.status_code != 200:
                logger.error(
                    'Failed to load danmakus for episode ID "%s": HTTP %s',
                    episode_id,
                    response.status_code,
                )
                return []

            data = response.json()
            comments = data.get("comments")
            if comments and isinstance(comments, list):
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
