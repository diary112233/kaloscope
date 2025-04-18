from dataclasses import dataclass

from app.core.flow.fields.base import Field


@dataclass(kw_only=True)
class DividerField(Field[None]):
    """A divider to separate the fields."""

    default: None = None

    def _field_type(self) -> str:
        return "divider"
