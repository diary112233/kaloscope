from dataclasses import dataclass

from app.core.flow.fields.base import Field


@dataclass(kw_only=True)
class URLField(Field[str]):
    """An input element that enables to enter a URL."""

    default: str = ""
    placeholder: str | None = None
    minlength: int = 0
    maxlength: int

    def _field_type(self) -> str:
        return "url"
