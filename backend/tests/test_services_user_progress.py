import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.media import MediaItem
from app.models.user import (
    HistoryEntry,
    HistoryType,
    MediaProgressQuery,
    MediaProgressSet,
    MediaProgressStatus,
    UserHistory,
    UserMediaProgress,
)
from app.services.user import UserHistoryService, UserMediaProgressService


def set_status(user, obj):
    return asyncio.run(UserMediaProgressService._set_status(user, obj))


@pytest.mark.parametrize(
    ("percentage", "status"),
    [
        (0, MediaProgressStatus.WATCHING),
        (20, MediaProgressStatus.WATCHING),
        (79, MediaProgressStatus.WATCHING),
        (80, MediaProgressStatus.WATCHED),
        (100, MediaProgressStatus.WATCHED),
    ],
)
def test_media_progress_status_from_percentage(
    percentage: int, status: MediaProgressStatus
):
    assert UserMediaProgressService.status_from_percentage(percentage) == status


def test_watched_status_is_sticky_when_percentage_decreases():
    assert (
        UserMediaProgressService.status_from_percentage(
            5, MediaProgressStatus.WATCHED
        )
        == MediaProgressStatus.WATCHED
    )


def test_list_media_progress_filters_restricted_libraries(monkeypatch):
    query_result = object()
    filter_mock = AsyncMock(return_value=query_result)
    dump_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(UserMediaProgress, "filter", filter_mock)
    monkeypatch.setattr(UserMediaProgressService, "dump_list", dump_mock)
    user = SimpleNamespace(
        id=7, perms=SimpleNamespace(media_lib_ids=[11, 13])
    )

    result = asyncio.run(
        UserMediaProgressService.list(user, MediaProgressQuery(ids=[2, 3]))
    )

    assert result == []
    filter_mock.assert_awaited_once_with(
        user_id=7,
        media_id__in=[2, 3],
        media__lib_id__in=[11, 13],
    )
    dump_mock.assert_awaited_once_with(query_result)


def test_progress_checkpoint_does_not_increment_history_repetitions(monkeypatch):
    history = SimpleNamespace(repetitions=4, save=AsyncMock())
    monkeypatch.setattr(
        UserHistoryService, "retention_days", AsyncMock(return_value=3)
    )
    update_mock = AsyncMock(return_value=(history, False))
    monkeypatch.setattr(UserHistory, "update_or_create", update_mock)

    result = asyncio.run(
        UserHistoryService.record(
            7,
            HistoryEntry(
                rel_type=HistoryType.VIDEO,
                rel_id=11,
                position=120,
                percentage=40,
            ),
            increment_repetitions=False,
        )
    )

    assert result is history
    assert history.repetitions == 4
    history.save.assert_not_awaited()


def test_set_watching_creates_zero_progress(monkeypatch):
    user = SimpleNamespace(id=7, perms=None)
    media = SimpleNamespace(id=11, parent_id=None)
    progress = object()
    monkeypatch.setattr(
        UserMediaProgressService, "_get_accessible_media", AsyncMock(return_value=media)
    )
    monkeypatch.setattr(UserMediaProgress, "get_or_none", AsyncMock(return_value=None))
    create_mock = AsyncMock(return_value=progress)
    monkeypatch.setattr(UserMediaProgress, "create", create_mock)
    sync_mock = AsyncMock()
    monkeypatch.setattr(UserMediaProgressService, "_sync_parent", sync_mock)

    result, parent = set_status(
        user,
        MediaProgressSet(media_id=11, status=MediaProgressStatus.WATCHING),
    )

    assert result is progress
    assert parent is None
    create_mock.assert_awaited_once_with(
        user_id=7,
        media_id=11,
        position=0,
        percentage=0,
        status=MediaProgressStatus.WATCHING,
        manual=True,
    )
    sync_mock.assert_not_awaited()


def test_set_watched_preserves_position(monkeypatch):
    user = SimpleNamespace(id=7, perms=None)
    media = SimpleNamespace(id=11, parent_id=None)
    progress = SimpleNamespace(
        position=321,
        percentage=35,
        status=MediaProgressStatus.WATCHING,
        manual=False,
        save=AsyncMock(),
    )
    monkeypatch.setattr(
        UserMediaProgressService, "_get_accessible_media", AsyncMock(return_value=media)
    )
    monkeypatch.setattr(
        UserMediaProgress, "get_or_none", AsyncMock(return_value=progress)
    )

    result, _ = set_status(
        user,
        MediaProgressSet(media_id=11, status=MediaProgressStatus.WATCHED),
    )

    assert result.position == 321
    assert result.percentage == 35
    assert result.status == MediaProgressStatus.WATCHED
    assert result.manual is True
    progress.save.assert_awaited_once_with(
        update_fields=["status", "manual", "updated_at"]
    )


def test_set_watching_preserves_existing_position_and_percentage(monkeypatch):
    user = SimpleNamespace(id=7, perms=None)
    media = SimpleNamespace(id=11, parent_id=None)
    progress = SimpleNamespace(
        position=840,
        percentage=100,
        status=MediaProgressStatus.WATCHED,
        manual=False,
        save=AsyncMock(),
    )
    monkeypatch.setattr(
        UserMediaProgressService, "_get_accessible_media", AsyncMock(return_value=media)
    )
    monkeypatch.setattr(
        UserMediaProgress, "get_or_none", AsyncMock(return_value=progress)
    )

    result, _ = set_status(
        user,
        MediaProgressSet(media_id=11, status=MediaProgressStatus.WATCHING),
    )

    assert result is progress
    assert progress.position == 840
    assert progress.percentage == 100
    assert progress.status == MediaProgressStatus.WATCHING
    assert progress.manual is True
    progress.save.assert_awaited_once_with(
        update_fields=["status", "manual", "updated_at"]
    )


def test_set_unwatched_preserves_progress(monkeypatch):
    user = SimpleNamespace(id=7, perms=None)
    media = SimpleNamespace(id=11, parent_id=None)
    progress = SimpleNamespace(
        position=456,
        percentage=62,
        status=MediaProgressStatus.WATCHING,
        manual=False,
        save=AsyncMock(),
    )
    monkeypatch.setattr(
        UserMediaProgressService, "_get_accessible_media", AsyncMock(return_value=media)
    )
    monkeypatch.setattr(
        UserMediaProgress, "get_or_none", AsyncMock(return_value=progress)
    )

    result, parent = set_status(
        user,
        MediaProgressSet(media_id=11, status=MediaProgressStatus.UNWATCHED),
    )

    assert result is progress
    assert parent is None
    assert progress.position == 456
    assert progress.percentage == 62
    assert progress.status == MediaProgressStatus.UNWATCHED
    assert progress.manual is True
    progress.save.assert_awaited_once_with(
        update_fields=["status", "manual", "updated_at"]
    )


def test_child_status_change_syncs_parent(monkeypatch):
    user = SimpleNamespace(id=7, perms=None)
    media = SimpleNamespace(id=11, parent_id=5)
    progress = object()
    parent_progress = object()
    monkeypatch.setattr(
        UserMediaProgressService, "_get_accessible_media", AsyncMock(return_value=media)
    )
    monkeypatch.setattr(UserMediaProgress, "get_or_none", AsyncMock(return_value=None))
    monkeypatch.setattr(UserMediaProgress, "create", AsyncMock(return_value=progress))
    sync_mock = AsyncMock(return_value=parent_progress)
    monkeypatch.setattr(UserMediaProgressService, "_sync_parent", sync_mock)

    result, parent = set_status(
        user,
        MediaProgressSet(media_id=11, status=MediaProgressStatus.WATCHING),
    )

    assert result is progress
    assert parent is parent_progress
    sync_mock.assert_awaited_once_with(7, media)


def test_sync_parent_deletes_automatic_progress_without_child_progress(monkeypatch):
    media = SimpleNamespace(parent_id=5)
    parent = SimpleNamespace(manual=False, delete=AsyncMock())
    children = [SimpleNamespace(id=11), SimpleNamespace(id=12)]
    monkeypatch.setattr(
        UserMediaProgress, "get_or_none", AsyncMock(return_value=parent)
    )
    monkeypatch.setattr(MediaItem, "filter", AsyncMock(return_value=children))
    monkeypatch.setattr(UserMediaProgress, "filter", AsyncMock(return_value=[]))

    result = asyncio.run(UserMediaProgressService._sync_parent(7, media))

    assert result is None
    parent.delete.assert_awaited_once()


def test_sync_parent_keeps_manual_parent(monkeypatch):
    media = SimpleNamespace(parent_id=5)
    parent = SimpleNamespace(manual=True)
    children_mock = AsyncMock()
    monkeypatch.setattr(
        UserMediaProgress, "get_or_none", AsyncMock(return_value=parent)
    )
    monkeypatch.setattr(MediaItem, "filter", children_mock)

    result = asyncio.run(UserMediaProgressService._sync_parent(7, media))

    assert result is parent
    children_mock.assert_not_awaited()


def test_mark_watched_delegates_to_status_service(monkeypatch):
    user = SimpleNamespace(id=7, perms=None)
    progress = object()
    parent = object()
    set_mock = AsyncMock(return_value=(progress, parent))
    monkeypatch.setattr(UserMediaProgressService, "set_status", set_mock)

    result = asyncio.run(
        UserMediaProgressService.mark_watched(
            user, SimpleNamespace(media_id=11)
        )
    )

    assert result == (progress, parent)
    status = set_mock.await_args.args[1]
    assert status.media_id == 11
    assert status.status == MediaProgressStatus.WATCHED
