from dataclasses import dataclass, field
from typing import Literal, TypedDict

from app.core.flow.fields.base import Field

# define the language type for the script field
type Language = Literal["python", "javascript"]


class Script(TypedDict):
    """The type for the script field."""

    language: Language
    code: str | None


@dataclass(kw_only=True)
class ScriptField(Field[Script]):
    """A control for script editing."""

    default: Script = field(
        default_factory=lambda: {"language": "python", "code": None}
    )
    placeholder: str | None = None
    tabsize: int = 4
    lineLength: int = 88
    darkmode: bool = True
    copier: bool = True
    resetter: bool = True
    formatter: bool = True

    def _field_type(self) -> str:
        return "script"
