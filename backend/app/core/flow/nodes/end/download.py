from typing import Any

from app.core.flow.fields import ToggleField
from app.core.flow.handles import InputHandle
from app.core.flow.nodes.base import CancellationSignal, Node, end_node
from app.models.flow import GraphCategory


@end_node(order=1, categories=(GraphCategory.DOWNLOAD,))
class DownloadEndNode(Node):
    force_end = ToggleField("force_end", tooltip="force_end", required=True)

    class Handles:
        input = InputHandle()

    @classmethod
    async def execute(cls, *, node_data: dict[str, Any], **kwargs):
        # force end the flow if required
        if cls.force_end.extract(node_data):
            raise CancellationSignal
