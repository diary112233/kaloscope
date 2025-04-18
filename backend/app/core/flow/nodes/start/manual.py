from app.core.flow.handles import OutputHandle
from app.core.flow.nodes.base import Node, start_node
from app.models.flow import GraphCategory


@start_node(order=1, categories=(GraphCategory.MANUAL,))
class ManualStartNode(Node):
    class Handles:
        output = OutputHandle()
