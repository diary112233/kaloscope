from app.core.flow.handles.base import Handle, HandlePosition, HandleType
from app.core.flow.handles.input import InputHandle
from app.core.flow.handles.output import OutputHandle

# return this from execute() to explicitly stop flow execution
STOP: OutputHandle = OutputHandle.create("__stop__")


class DefaultHandles:
    """The default input and output handles of a node."""

    input = InputHandle()
    output = OutputHandle()


__all__ = [
    "Handle",
    "HandlePosition",
    "HandleType",
    "InputHandle",
    "OutputHandle",
    "DefaultHandles",
    "STOP",
]
