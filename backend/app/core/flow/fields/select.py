from dataclasses import dataclass

from app.core.flow.fields.base import Field


@dataclass(kw_only=True)
class SelectField(Field[str | int | bool]):
    """A control for selecting amongst a set of options."""

    placeholder: str | None = None
    options: dict[str, str | int | bool]

    def _field_type(self) -> str:
        return "select"
