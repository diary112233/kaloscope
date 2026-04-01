from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.core.constants import ENCODING
from app.core.flow.fields.base import Field

# define the language type for the code field
type Language = Literal["yaml", "json", "jsonc", "jinja2", "python", "javascript"]


@dataclass(kw_only=True)
class CodeField(Field[str]):
    """A control for code editing."""

    default: Path | str = ""
    template: str | None = None
    placeholder: str | None = None
    language: Language | None = None
    tabsize: int = 2
    lineLength: int = 80
    collapse: bool = False
    readonly: bool = False
    darkmode: bool = False
    copier: bool = True
    resetter: bool = True
    formatter: bool = True
    width: str | None = "24rem"

    def _field_type(self) -> str:
        return "code"

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.default, Path) and self.default.is_file():
            with open(self.default, encoding=ENCODING) as f:
                self.default = f.read()
