from dataclasses import asdict
from pathlib import Path

import aiofiles
from tortoise import timezone
from tortoise.expressions import Q
from tortoise.functions import Count, Sum
from tortoise.transactions import atomic

from app.core.constants import ENCODING
from app.core.dl.adapter import load_config
from app.core.dl.syncer import Unique
from app.core.exceptions import ErrorCode, KaloscopeException
from app.models.download import (
    DownloadAdd,
    DownloadDir,
    Downloader,
    DownloaderBasics,
    DownloadState,
    DownloadStats,
    DownloadTask,
)
from app.models.flow import FlowTrigger, GraphCategory
from app.services.base import BaseService
from app.services.flow import FlowTriggerService
from app.utils.bittorrent import (
    decode_torrent,
    standardize_magnet,
)


class DownloaderService(BaseService[Downloader], model=Downloader):
    """The service class for all download manager related operations."""

    PRESETS_PATH = Path(__file__).resolve().parents[2] / "static/downloaders"

    @classmethod
    async def get_presets(cls) -> dict[str, str]:
        """Get the download manager presets.

        Returns:
            The download manager presets.
        """
        presets = {}
        for file in cls.PRESETS_PATH.iterdir():
            if file.is_file() and file.suffix == ".yaml":
                async with aiofiles.open(file, encoding=ENCODING) as f:
                    presets[file.name[:-5]] = await f.read()
        return presets

    @classmethod
    @atomic()
    async def update_priorities(cls, ids: list):
        """Update the download manager priorities.

        Args:
            ids: The sorted download manager IDs.
        """
        managers = await Downloader.filter(id__in=ids)
        # avoid duplicate priorities
        priorities = [manager.priority for manager in managers]
        start_priority = 1 if min(priorities) > len(ids) else max(priorities) + 1
        for manager in managers:
            manager.priority = start_priority + ids.index(manager.id)
        await Downloader.bulk_update(managers, fields=["priority"])

    @classmethod
    @atomic()
    async def upsert_basics(cls, basics: DownloaderBasics) -> Downloader:
        """Create or update the download manager basics.

        Args:
            basics: The download manager basics.

        Raises:
            KaloscopeException: If the name already exists.

        Returns:
            The download manager instance.
        """
        # load the YAML configuration
        adapter = load_config(basics.config)

        # check if the name already exists
        filter = Q(name=adapter.name)
        if basics.id:
            filter &= ~Q(id=basics.id)
        if await Downloader.filter(filter).count() > 0:
            raise KaloscopeException(ErrorCode.NAME_ALREADY_EXISTS)

        if basics.id:
            # update the download manager
            await Downloader.filter(id=basics.id).update(
                config=basics.config,
                name=adapter.name,
                host=adapter.host,
                port=adapter.port,
            )
            manager = await Downloader.get(id=basics.id)
        else:
            # create the download manager
            version = await adapter.version()
            priorities: list = await Downloader.all().values_list("priority", flat=True)
            manager = Downloader(
                preset=basics.preset or None,
                config=basics.config,
                name=adapter.name,
                host=adapter.host,
                port=adapter.port,
                version=version,
                priority=(max(priorities) + 1 if priorities else 1),
            )
            await manager.save()

        # bind the flow triggers to the download manager
        await FlowTriggerService.bind_triggers(
            GraphCategory.DOWNLOAD, manager.id, basics.triggers
        )

        return manager

    @classmethod
    @atomic()
    async def delete(cls, id: int):
        """Delete a download manager.

        Args:
            id: The download manager ID.
        """
        await Downloader.filter(id=id).delete()
        await FlowTrigger.filter(category=GraphCategory.DOWNLOAD, rel_id=id).delete()


class DownloadDirService(BaseService[DownloadDir], model=DownloadDir):
    """The service class for all download directory related operations."""

    @classmethod
    async def upsert_dir(cls, path: str) -> DownloadDir:
        """Create or update the download directory.

        Args:
            path: The download directory path.

        Returns:
            The download directory instance.
        """
        dir = await DownloadDir.get_or_none(path=path)
        if dir is not None:
            dir.last_used = timezone.now()
            await dir.save()
            return dir
        return await DownloadDir.create(path=path, last_used=timezone.now())


class DownloadTaskService(BaseService[DownloadTask], model=DownloadTask):
    """The service class for all download task related operations."""

    @classmethod
    async def hash_collision(cls, hash: str | None, hash_v2: str | None = None) -> bool:
        """Check if the info hash already exists.

        Args:
            hash: The info hash.
            hash_v2: The info hash v2.

        Returns:
            True if the info hash already exists, False otherwise.
        """
        if hash and await DownloadTask.filter(info_hash=hash).exists():
            return True
        return bool(
            hash_v2 and await DownloadTask.filter(info_hash_v2=hash_v2).exists()
        )

    @classmethod
    @atomic()
    async def add(cls, add: DownloadAdd) -> DownloadTask:
        """Add a download task.

        Args:
            add: The download task details.

        Returns:
            The added download task.
        """
        manager = await Downloader.get(id=add.downloader_id)
        adapter = load_config(manager.config)

        # call the `add_torrent` or `add_link` method
        info_hash, info_hash_v2, magnet_link, result = None, None, None, None
        if add.torrent and (torrent := decode_torrent(add.torrent.body)) is not None:
            # extract info hash from the torrent
            info_hash = torrent.info_hash
            magnet_link = torrent.magnet_link
            if await cls.hash_collision(info_hash):
                raise KaloscopeException(ErrorCode.INFO_HASH_COLLISION)
            result = await adapter.call("add_torrent", add.model_dump())
        elif add.link and (magnet := standardize_magnet(add.link)) is not None:
            # extract info hash from the magnet link
            add.link = magnet.link
            info_hash = magnet.info_hash
            info_hash_v2 = magnet.info_hash_v2
            magnet_link = magnet.link
            if await cls.hash_collision(info_hash, info_hash_v2):
                raise KaloscopeException(ErrorCode.INFO_HASH_COLLISION)
            result = await adapter.call("add_link", add.model_dump())
        if not info_hash and not info_hash_v2:
            raise KaloscopeException(ErrorCode.GET_INFO_HASH_FAILED)

        # save the download directory
        await DownloadDirService.upsert_dir(add.dir)
        # create the download task
        unique_id = result.get("unique_id") if isinstance(result, dict) else None
        return await DownloadTask.create(
            downloader_id=manager.id,
            dir=add.dir,
            name=info_hash or info_hash_v2,
            unique_id=unique_id,
            info_hash=info_hash,
            info_hash_v2=info_hash_v2,
            magnet_link=magnet_link,
            state=DownloadState.PAUSED if add.pause else DownloadState.DOWNLOADING,
        )

    @classmethod
    async def pause(cls, id: int):
        """Pause a download task.

        Args:
            id: The download task ID.
        """
        task = await DownloadTask.get(id=id)
        manager = await Downloader.get(id=task.downloader_id)
        adapter = load_config(manager.config)
        await adapter.call("pause", asdict(Unique.from_task(task)))
        await DownloadTask.filter(id=id).update(state=DownloadState.PAUSED)

    @classmethod
    async def start(cls, id: int):
        """Start a download task.

        Args:
            id: The download task ID.
        """
        task = await DownloadTask.get(id=id)
        manager = await Downloader.get(id=task.downloader_id)
        adapter = load_config(manager.config)
        await adapter.call("start", asdict(Unique.from_task(task)))
        await DownloadTask.filter(id=id).update(state=DownloadState.DOWNLOADING)

    @classmethod
    async def delete(cls, id: int, local: bool = False):
        """Delete a download task.

        Args:
            id: The download task ID.
            local: Whether to delete the local files.
        """
        task = await DownloadTask.get(id=id)
        manager = await Downloader.get(id=task.downloader_id)
        adapter = load_config(manager.config)
        await adapter.call("delete", {**asdict(Unique.from_task(task)), "local": local})
        await DownloadTask.filter(id=id).delete()

    @classmethod
    async def stats(cls) -> DownloadStats:
        """Get the download statistics.

        Returns:
            The download statistics object.
        """
        count = (
            await DownloadTask.annotate(count=Count("id"))
            .group_by("state")
            .values("state", "count")
        )
        downloading = sum(
            c["count"] for c in count if c["state"] != DownloadState.COMPLETED
        )
        completed = sum(
            c["count"] for c in count if c["state"] == DownloadState.COMPLETED
        )
        up_speed = (
            await DownloadTask.annotate(total_up=Sum("up_speed"))
            .filter(state=DownloadState.DOWNLOADING)
            .values("total_up")
        )[0]["total_up"] or 0
        dl_speed = (
            await DownloadTask.annotate(total_dl=Sum("dl_speed"))
            .filter(state=DownloadState.DOWNLOADING)
            .values("total_dl")
        )[0]["total_dl"] or 0
        return DownloadStats(
            downloading=downloading,
            completed=completed,
            up_speed=up_speed,
            dl_speed=dl_speed,
        )
