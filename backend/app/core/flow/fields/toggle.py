from dataclasses import dataclass

from app.core.flow.fields.base import Field


@dataclass(kw_only=True)
class ToggleField(Field[bool]):
    """A control for toggling between two states."""

    default: bool = False

    def _field_type(self) -> str:
        return "toggle"
