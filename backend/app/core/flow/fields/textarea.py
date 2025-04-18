from dataclasses import dataclass

from app.core.flow.fields.base import Field


@dataclass(kw_only=True)
class TextareaField(Field[str]):
    """An input element that enables to enter multiple lines of text."""

    default: str = ""
    placeholder: str | None = None
    minlength: int = 0
    maxlength: int | None = None
    rows: int = 2

    def _field_type(self) -> str:
        return "textarea"
