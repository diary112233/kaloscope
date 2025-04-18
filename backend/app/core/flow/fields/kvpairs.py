from dataclasses import dataclass
from typing import TypedDict

from app.core.flow.fields.base import Field


class KVPair(TypedDict):
    """The type for the key-value pair."""

    key: str
    value: str


@dataclass(kw_only=True)
class KVPairsField(Field[tuple[KVPair, ...]]):
    """A control for adding key-value pairs."""

    default: tuple[KVPair, ...] = ()
    placeholder: tuple[str | None, str | None] | None = None

    def _field_type(self) -> str:
        return "kvpairs"
