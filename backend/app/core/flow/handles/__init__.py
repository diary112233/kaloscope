from app.core.flow.handles.base import Handle, HandlePosition, HandleType
from app.core.flow.handles.input import InputHandle
from app.core.flow.handles.output import OutputHandle


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
]
