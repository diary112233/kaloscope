from tortoise.expressions import Q
from tortoise.transactions import atomic

from app.core.exceptions import ErrorCode, KaloscopeException
from app.core.media.watcher import LibWatcher
from app.models.flow import FlowTrigger, GraphCategory
from app.models.media import MediaItem, MediaLib, MediaLibBasics
from app.services.base import BaseService
from app.services.flow import FlowTriggerService


class MediaLibService(BaseService[MediaLib], model=MediaLib):
    """The service class for all media library related operations."""

    @classmethod
    @atomic()
    async def update_priorities(cls, ids: list):
        """Update the media library priorities.

        Args:
            ids: The sorted media library IDs.
        """
        libs = await MediaLib.filter(id__in=ids)
        # avoid duplicate priorities
        priorities = [lib.priority for lib in libs]
        start_priority = 1 if min(priorities) > len(ids) else max(priorities) + 1
        for lib in libs:
            lib.priority = start_priority + ids.index(lib.id)
        await MediaLib.bulk_update(libs, fields=["priority"])

    @classmethod
    @atomic()
    async def upsert_basics(cls, basics: MediaLibBasics) -> MediaLib:
        """Create or update the media library basics.

        Args:
            basics: The media library basics.

        Raises:
            KaloscopeException: If the name or directory already exists.

        Returns:
            The media library instance.
        """

        # check if the name or directory already exists
        filter = ~Q(id=basics.id) if basics.id else Q()
        if await MediaLib.filter(filter & Q(name=basics.name)).count() > 0:
            raise KaloscopeException(ErrorCode.NAME_ALREADY_EXISTS)
        if basics.dir and await MediaLib.filter(filter & Q(dir=basics.dir)).count() > 0:
            raise KaloscopeException(ErrorCode.DIRECTORY_ALREADY_EXISTS)

        if basics.id:
            # update the media library
            await MediaLib.filter(id=basics.id).update(
                name=basics.name,
                language=basics.language or None,
            )
            lib = await MediaLib.get(id=basics.id)
        else:
            # create the media library
            priorities: list = await MediaLib.all().values_list("priority", flat=True)
            lib = MediaLib(
                lib_type=basics.lib_type,
                name=basics.name,
                dir=basics.dir,
                language=basics.language or None,
                priority=(max(priorities) + 1 if len(priorities) > 0 else 1),
            )
            await lib.save()
            watcher: LibWatcher = cls.app_ctx().watcher
            await watcher.add_observer(lib, initialize=True)

        # bind the flow triggers to the media library
        await FlowTriggerService.bind_triggers(
            GraphCategory.INGEST, lib.id, basics.triggers
        )

        return lib

    @classmethod
    @atomic()
    async def delete(cls, id: int):
        """Delete a media library.

        Args:
            id: The media library ID.
        """
        lib = await MediaLib.get(id=id)
        await MediaLib.filter(id=id).delete()
        await FlowTrigger.filter(category=GraphCategory.INGEST, rel_id=id).delete()
        # remove the observer
        watcher: LibWatcher = cls.app_ctx().watcher
        await watcher.remove_observer(lib.dir)


class MediaItemService(BaseService[MediaItem], model=MediaItem):
    """The service class for all media item related operations."""

    pass
