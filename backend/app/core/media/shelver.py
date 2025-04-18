from pathlib import Path

import aiofiles
from lxml import etree
from sanic.log import logger
from watchdog.events import EVENT_TYPE_CREATED, EVENT_TYPE_MOVED

from app.core.constants import ENCODING
from app.core.flow.context import RETVAL_KEY, Context
from app.core.renderer import render
from app.models.media import NFOType

TEMPLATES_PATH = Path(__file__).resolve().parents[3] / "static/templates/nfo"


async def gen_nfo(context: Context, tmpl: NFOType):
    """Generate NFO file for the given context and template type.

    Args:
        context: Context of the flow execution.
        tmpl: Template type to use for NFO generation.
    """
    # only generate NFO for created or moved items
    event_type = context.bootparams.get("event_type")
    if event_type not in (EVENT_TYPE_CREATED, EVENT_TYPE_MOVED):
        return
    # ensure we have item path and name
    item = context.bootparams.get("item", {})
    item_path = item.get("path")
    item_name = item.get("name")
    if not item_path or not item_name:
        return
    # ensure we have return value
    retval = context.get(RETVAL_KEY)
    if not retval or not isinstance(retval, list):
        return
    # check if NFO file is locked
    nfo_path = Path(item_path).parent / f"{item_name}.nfo"
    if is_locked(nfo_path):
        logger.info("NFO file is locked, skipping generation: %s", nfo_path)
        return
    # generate NFO file
    tmpl_path = TEMPLATES_PATH / f"{tmpl.value}.nfo"
    async with aiofiles.open(tmpl_path, encoding=ENCODING) as f:
        template = await f.read()
    async with aiofiles.open(nfo_path, "w", encoding=ENCODING) as f:
        await f.write(render(template, context=retval[0]))


def is_locked(nfo_path: Path) -> bool:
    """Check if the NFO file is locked by reading the <lockdata> tag.

    Args:
        nfo_path: Path to the NFO file.

    Returns:
        True if the NFO file is locked, False otherwise.
    """
    if not nfo_path.exists():
        return False
    try:
        for _, element in etree.iterparse(nfo_path, events=("end",)):
            if element.tag == "lockdata":
                text = element.text
                element.clear()
                return text and text.lower() == "true"
        return False
    except Exception:
        logger.error("Failed to read existing NFO file!", exc_info=True)
        return False
