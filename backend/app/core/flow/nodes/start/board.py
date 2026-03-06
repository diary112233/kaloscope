from app.core.flow.fields import CodeField
from app.core.flow.handles import OutputHandle
from app.core.flow.nodes.base import TEMPLATES_PATH, Node, start_node
from app.models.flow import GraphCategory


@start_node(order=2, icon="appsListDetail", categories=(GraphCategory.INDEXER,))
class BoardStartNode(Node):
    config = CodeField(
        "config",
        language="yaml",
        darkmode=True,
        default=TEMPLATES_PATH / "conf/board.yaml",
    )

    class Handles:
        output = OutputHandle(tag="board")
