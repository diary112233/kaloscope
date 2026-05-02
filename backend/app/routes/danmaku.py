from sanic import Blueprint, HTTPResponse, json
from sanic_ext import validate

from app.models.media import MediaResource
from app.services.danmaku import DanmakuService

# subroutes for all danmaku related operations
danmaku = Blueprint("danmaku", url_prefix="/danmaku")


@danmaku.post("/match")
@validate(json=MediaResource)
async def match_danmakus(_, body: MediaResource) -> HTTPResponse:
    """Match danmakus for the given media resource."""
    danmakus = await DanmakuService.match_danmakus(body.path)
    return json([danmaku.model_dump() for danmaku in danmakus])


@danmaku.post("/search/episodes")
async def search_episodes(_) -> HTTPResponse:
    """Search for episodes matching the given criteria."""
    # TODO: implement episode search API
    return json({})


@danmaku.get("/comment/<episode_id:int>")
async def get_danmakus(_, episode_id: int) -> HTTPResponse:
    """Get the danmakus for the given episode ID."""
    # TODO: implement comment retrieval API
    return json({})
