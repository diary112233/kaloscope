import sys

from sanic import Blueprint, HTTPResponse, json

# subroutes for all system related operations
system = Blueprint("system", url_prefix="/system")


@system.get("/platform")
async def get_platform(_) -> HTTPResponse:
    """Get the current platform."""
    return json({"platform": sys.platform})
