from app.core.flow.fields import CodeField
from app.core.flow.handles import OutputHandle
from app.core.flow.nodes.base import TEMPLATES_PATH, Node, start_node
from app.models.flow import GraphCategory


@start_node(order=3, icon="boxMultipleSearch", categories=(GraphCategory.INDEXER,))
class SearchStartNode(Node):
    example = CodeField(
        "request_example",
        language="jsonc",
        collapse=True,
        readonly=True,
        template="req/search.jsonc",
    )
    config = CodeField(
        "config",
        language="yaml",
        darkmode=True,
        default=TEMPLATES_PATH / "conf/search.yaml",
    )

    class Handles:
        output = OutputHandle(tag="search")
