from typing import Any

import STPyV8

from app.core.flow.context import Context
from app.core.flow.fields import ScriptField
from app.core.flow.nodes.base import Node, general_node


@general_node(order=3, icon="code")
class ScriptNode(Node):
    script = ScriptField("code", required=True)

    @classmethod
    async def execute(
        cls, *, node_id: str, node_data: dict[str, Any], context: Context, **kwargs
    ):
        script = cls.script.extract(node_data)
        if (script_code := script["code"]) is None:
            return
        language = script["language"]
        if language == "python":
            # https://docs.python.org/3/library/functions.html#exec
            namespace = {
                "node_id": node_id,
                "node_data": node_data,
                "context": context,
            }
            exec(f"{script_code}\n\nexecute(node_id, node_data, context)", namespace)
        elif language == "javascript":
            # https://github.com/cloudflare/stpyv8
            with STPyV8.JSContext() as js_ctx:
                js_ctx.eval(script_code)
                js_ctx.locals.execute(node_id, node_data, context)
