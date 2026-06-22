"""Unit tests for the flow script node."""

import asyncio
from types import SimpleNamespace

from app.core.config import KaloscopeConfig
from app.core.flow.context import Context
from app.core.flow.nodes.general.script import ScriptNode
from app.utils.dict import TrackableDict


def _context(storage: dict):
    ctx = Context.__new__(Context)
    ctx.globalvars = {}
    ctx.localvars = {}
    ctx.bootparams = {}
    ctx.storage = TrackableDict(storage)
    ctx.union()
    return ctx


def test_js_script_values():
    ctx = _context(
        {"term": "", "count": 1, "info": {"term": "", "count": 2, "items": [1, "x"]}}
    )
    node_data = {
        "term": "",
        "count": 3,
        "info": {"items": [2]},
        "script": {
            "language": "javascript",
            "code": """
            function execute(node_id, node_data, context) {
              const termOk = node_data.term === "" && context.term === "";
              const total = node_data.count + context.count;
              const info = context.info;

              node_data.term = termOk ? "ok" : "bad";
              node_data.count = total;
              node_data.info.items.push(info.items[0]);

              context.term = termOk ? "ok" : "bad";
              context.count = total + info.count;
              context.info.term = info.term === "";
              context.info.items.push("y");
            }
            """,
        },
    }

    asyncio.run(
        ScriptNode.execute(node_id="script-node", node_data=node_data, context=ctx)
    )

    assert node_data["term"] == "ok"
    assert node_data["count"] == 4
    assert node_data["info"] == {"items": [2, 1]}
    assert ctx.storage == {
        "term": "ok",
        "count": 6,
        "info": {"term": True, "count": 2, "items": [1, "x", "y"]},
    }


def test_python_script_values(monkeypatch):
    monkeypatch.setattr(
        KaloscopeConfig,
        "get",
        staticmethod(lambda: SimpleNamespace(script_strict_mode=False)),
    )
    ctx = _context(
        {"term": "", "count": 1, "info": {"term": "", "count": 2, "items": [1, "x"]}}
    )
    node_data = {
        "term": "",
        "count": 3,
        "info": {"items": [2]},
        "script": {
            "language": "python",
            "code": """
def execute(node_id, node_data, context):
    term_ok = node_data["term"] == "" and context["term"] == ""
    total = node_data["count"] + context["count"]
    info = context["info"]

    node_data["term"] = "ok" if term_ok else "bad"
    node_data["count"] = total
    node_data["info"]["items"].append(info["items"][0])

    context["term"] = "ok" if term_ok else "bad"
    context["count"] = total + info["count"]
    info["term"] = info["term"] == ""
    info["items"].append("y")
    context["info"] = info
            """,
        },
    }

    asyncio.run(
        ScriptNode.execute(node_id="script-node", node_data=node_data, context=ctx)
    )

    assert node_data["term"] == "ok"
    assert node_data["count"] == 4
    assert node_data["info"] == {"items": [2, 1]}
    assert ctx.storage == {
        "term": "ok",
        "count": 6,
        "info": {"term": True, "count": 2, "items": [1, "x", "y"]},
    }
