from app.core.flow.fields.code import CodeField
from app.core.flow.handles import OutputHandle
from app.core.flow.nodes.base import Node, start_node
from app.models.flow import GraphCategory


@start_node(order=1, icon="boxMultipleSearch", categories=(GraphCategory.INGEST,))
class IngestStartNode(Node):
    example = CodeField(
        "request_example",
        language="jsonc",
        collapse=False,
        readonly=True,
        template="req/ingest.jsonc",
    )

    class Handles:
        output = OutputHandle()
