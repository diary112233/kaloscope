from typing import Any

from app.core.flow.context import Context
from app.core.flow.fields.code import CodeField
from app.core.flow.fields.select import SelectField
from app.core.flow.fields.text import TextField
from app.core.flow.nodes.base import Node, general_node


@general_node(order=2, icon="documentSignature")
class TextNode(Node):
    path = TextField("path", required=True, maxlength=1024)
    mode = SelectField(
        required=True,
        options={
            "exclusive": "x",
            "overwrite": "w",
            "append": "a",
        },
        default="x",
    )
    content = CodeField(required=True, language="jinja2", darkmode=True)

    @classmethod
    async def execute(cls, *, node_data: dict[str, Any], context: Context, **kwargs):
        return None
