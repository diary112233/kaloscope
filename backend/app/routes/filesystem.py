import os
from mimetypes import guess_file_type
from pathlib import Path

from pydantic import BaseModel
from sanic import Blueprint, HTTPResponse, json
from sanic_ext import validate

from app.core.exceptions import BadRequestException
from app.utils.disk import disk_usage, format_bytes

# the concatenation of the drive and root
ANCHOR = Path(__file__).anchor

# subroutes for all filesystem related operations
filesystem = Blueprint("filesystem", url_prefix="/filesystem")


class ListRequest(BaseModel):
    """Request model for listing files in a directory."""

    path: str | None = None
    only_dirs: bool = False


@filesystem.get("/list")
@validate(query=ListRequest)
async def list_files(_, query: ListRequest) -> HTTPResponse:
    """List the files in the given directory."""
    path = Path(query.path or ANCHOR)
    if not os.access(path, os.R_OK) or not path.is_dir():
        raise BadRequestException

    def readable(p: Path):
        try:
            return os.access(p, os.R_OK) and (not query.only_dirs or p.is_dir())
        except OSError:
            return False

    def is_empty(p: Path):
        try:
            return not any(filter(readable, p.iterdir()))
        except OSError:
            return True

    files = filter(readable, path.iterdir())
    return json(
        [
            {
                "name": file.name,
                "path": str(file.resolve()),
                "is_dir": file.is_dir(),
                "is_empty": is_empty(file) if file.is_dir() else None,
                "file_type": guess_file_type(file)[0] if file.is_file() else None,
            }
            for file in sorted(files, key=lambda f: (not f.is_dir(), f.name))
        ]
    )


class StatsRequest(BaseModel):
    """Request model for getting path statistics."""

    path: str


@filesystem.get("/stats")
@validate(query=StatsRequest)
async def get_stats(_, query: StatsRequest) -> HTTPResponse:
    """Get the statistics of the given path."""
    path = Path(query.path)
    if not os.access(path, os.R_OK):
        raise BadRequestException

    absolute_path = str(path.resolve())
    stats = {
        "name": path.name,
        "path": absolute_path,
        "is_dir": path.is_dir(),
        "readable": True,  # os.access(path, os.R_OK),
        "writable": os.access(path, os.W_OK),
        "size": format_bytes(path.stat().st_size),
    }
    if path.is_dir():
        usage = disk_usage(absolute_path)
        stats["total"] = usage.total_space()
        stats["used"] = usage.used_space()
        stats["free"] = usage.free_space()
    return json(stats)
