from typing import Any

from app.core.flow.context import Context
from app.core.flow.fields.code import CodeField
from app.core.flow.nodes.base import Node, general_node
from app.utils import json


@general_node(order=3, icon="bracesVariable")
class VariablesNode(Node):
    variables = CodeField(
        "variables",
        language="jinja2",
        darkmode=True,
        default="{}",
    )

    @classmethod
    async def execute(cls, *, node_data: dict[str, Any], context: Context, **kwargs):
        variables = cls.variables.extract(node_data, context=context)
        if not variables:
            return

        # merge the rendered variables into context
        if isinstance((obj := json.try_loads(variables, with_comments=True)), dict):
            context.update(obj)
