from typing import Any

from app.core.flow.context import RETVAL_KEY, Context
from app.core.flow.fields import ToggleField
from app.core.flow.fields.code import CodeField
from app.core.flow.handles import InputHandle
from app.core.flow.nodes.base import CancellationSignal, Node, end_node
from app.core.media.shelver import gen_nfo
from app.models.flow import GraphCategory
from app.models.media import NFOType
from app.utils import json


@end_node(order=5, icon="artist", categories=(GraphCategory.INGEST,))
class ArtistNode(Node):
    example = CodeField(
        "response_example",
        language="jsonc",
        collapse=True,
        readonly=True,
        template="nfo/artist.jsonc",
    )
    response = CodeField(
        "response",
        required=True,
        language="jinja2",
        darkmode=True,
        default=json.pretty([{"name": ""}]),
    )
    force_end = ToggleField("force_end", tooltip="force_end", required=True)

    class Handles:
        input = InputHandle()

    @classmethod
    async def execute(cls, *, node_data: dict[str, Any], context: Context, **kwargs):
        # extract the response
        context[RETVAL_KEY] = json.try_loads(
            cls.response.extract(node_data, context=context), with_comments=True
        )
        # generate NFO file
        await gen_nfo(context, NFOType.ARTIST)
        # force end the flow if required
        if cls.force_end.extract(node_data):
            raise CancellationSignal
