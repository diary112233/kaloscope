from dataclasses import dataclass

from app.core.flow.fields.base import Field


@dataclass(kw_only=True)
class NumberField(Field[float]):
    """An input element that enables to enter a number."""

    default: float = 0
    min: float | None = None
    max: float | None = None
    step: float = 1
    precision: int = 0

    def _field_type(self) -> str:
        return "number"
