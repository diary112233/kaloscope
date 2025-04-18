import asyncio
from datetime import datetime

from sanic import Blueprint, HTTPResponse, Request, empty, json
from sanic.log import logger
from sanic_ext import validate
from tortoise.expressions import Q

from app.core.config import KaloscopeConfig
from app.core.dl.adapter import load_config
from app.core.dl.syncer import DLSyncer
from app.models.base import IDs
from app.models.download import (
    DownloadAdd,
    DownloadDel,
    DownloadDir,
    Downloader,
    DownloaderBasics,
    DownloadQuery,
    DownloadTask,
)
from app.models.flow import GraphCategory
from app.services.download import DownloaderService, DownloadTaskService
from app.services.flow import FlowTriggerService
from app.utils.disk import disk_usage

# subroutes for all download related operations
download = Blueprint("download", url_prefix="/download")


@download.get("/manager/list")
async def list_managers(_) -> HTTPResponse:
    """List the download managers."""
    managers = await DownloaderService.dump_list(await Downloader.all())
    for manager in managers:
        # attach the list of flow triggers
        manager["triggers"] = await FlowTriggerService.get_triggers(
            GraphCategory.DOWNLOAD, manager["id"]
        )
        # check if the download manager is up or down
        adapter = load_config(manager["config"])
        if not adapter.methods.get("version"):
            manager["status"] = "unknown"
            continue
        version = await adapter.version()
        manager["status"] = "up" if version else "down"
        if version and manager["version"] != version:
            manager["version"] = version
            await Downloader.filter(id=manager["id"]).update(version=version)
    return json(managers)


@download.post("/manager/sort")
@validate(json=IDs)
async def sort_managers(_, body: IDs) -> HTTPResponse:
    """Sort the download managers."""
    await DownloaderService.update_priorities(body.ids)
    return empty()


@download.get("/manager/presets")
async def get_manager_presets(_) -> HTTPResponse:
    """Get the download manager presets."""
    return json(await DownloaderService.get_presets())


@download.post("/manager/upsert")
@validate(json=DownloaderBasics)
async def upsert_manager_basics(_, body: DownloaderBasics) -> HTTPResponse:
    """Create or update the download manager basics."""
    return json(
        await DownloaderService.dump(await DownloaderService.upsert_basics(body))
    )


@download.post("/manager/delete")
@validate(json=IDs)
async def delete_managers(_, body: IDs) -> HTTPResponse:
    """Delete the download managers."""
    for id in body.ids:
        try:
            await DownloaderService.delete(int(id))
        except Exception as e:
            if len(body.ids) == 1:
                raise e
            logger.error("Failed to delete the download manager: %s", id, exc_info=True)
    return empty()


@download.get("/dir/list")
async def list_directories(_) -> HTTPResponse:
    """List the download directories."""
    directories = await DownloadDir.all().order_by("-last_used").limit(3).values("path")
    if not directories:
        directories = [{"path": KaloscopeConfig.get_workspace("downloads")}]
    for directory in directories:
        directory["free"] = disk_usage(directory["path"]).free_space()
    return json(directories)


@download.get("/list")
@validate(query=DownloadQuery)
async def list_tasks(_, query: DownloadQuery) -> HTTPResponse:
    """List the download tasks."""
    queries = []
    if query.name:
        queries.append(Q(name__icontains=query.name))
    if query.state:
        queries.append(Q(state=query.state))
    if query.states:
        queries.append(Q(state__in=query.states))
    if query.downloader_id:
        queries.append(Q(downloader_id=query.downloader_id))
    page = await DownloadTask.page(*queries, **query.page_params)
    return json(await DownloadTaskService.dump_page(page))


@download.post("/add")
@validate(form=DownloadAdd)
async def add_task(_, body: DownloadAdd) -> HTTPResponse:
    """Add a download task."""
    return json(await DownloadTaskService.dump(await DownloadTaskService.add(body)))


@download.post("/pause")
@validate(json=IDs)
async def pause_tasks(_, body: IDs) -> HTTPResponse:
    """Pause the download tasks."""
    for id in body.ids:
        try:
            await DownloadTaskService.pause(int(id))
        except Exception as e:
            if len(body.ids) == 1:
                raise e
            logger.error("Failed to pause the download task: %s", id, exc_info=True)
    return empty()


@download.post("/start")
@validate(json=IDs)
async def start_tasks(_, body: IDs) -> HTTPResponse:
    """Start the download tasks."""
    for id in body.ids:
        try:
            await DownloadTaskService.start(int(id))
        except Exception as e:
            if len(body.ids) == 1:
                raise e
            logger.error("Failed to start the download task: %s", id, exc_info=True)
    return empty()


@download.post("/delete")
@validate(json=DownloadDel)
async def delete_tasks(_, body: DownloadDel) -> HTTPResponse:
    """Delete the download tasks."""
    for id in body.ids:
        try:
            await DownloadTaskService.delete(int(id), body.local)
        except Exception as e:
            if len(body.ids) == 1:
                raise e
            logger.error("Failed to delete the download task: %s", id, exc_info=True)
    return empty()


@download.get("/stats")
async def get_stats(request: Request):
    """Get the download statistics."""
    syncer: DLSyncer = request.app.ctx.syncer
    syncer.accelerate()
    try:
        start = datetime.now()
        response = await request.respond(
            headers={"Cache-Control": "no-cache"}, content_type="text/event-stream"
        )
        if response:
            while True:
                data = await DownloadTaskService.stats()
                await response.send(f"data: {data.model_dump_json()}\n\n")
                await asyncio.sleep(1)
                if (datetime.now() - start).total_seconds() > 60:
                    # stop the event stream every 60 seconds
                    break
    finally:
        syncer.decelerate()
