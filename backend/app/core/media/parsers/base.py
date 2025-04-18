import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from lxml import etree
from sanic.log import Colors, logger

from app.models.media import LibType

# the mime type for NFO files
NFO_MIME_TYPE = "text/x-nfo"


@dataclass(kw_only=True)
class MediaMeta:
    """The metadata of a media item parsed from an NFO file."""

    path: str = field(init=False, repr=False)
    title: str | None = None
    cover: str | None = None
    backdrop: str | None = None
    year: int | None = None
    rating: Decimal | None = None


class NFOParser(ABC):
    """The base class for NFO parsers."""

    @classmethod
    def is_nfo(cls, path: Path | str) -> bool:
        """Check if the path is an NFO file.

        Args:
            path: The path to check.

        Returns:
            True if the path is an NFO file, False otherwise.
        """
        if not isinstance(path, Path):
            path = Path(path)
        mime_type, _ = mimetypes.guess_file_type(path)
        return mime_type == NFO_MIME_TYPE

    async def parse(self, path: Path | str) -> MediaMeta:
        """Parse the NFO file at the given path.

        Args:
            path: The path to the NFO file.

        Returns:
            The parsed metadata as a MediaMeta object.
        """
        data = None
        if not isinstance(path, Path):
            path = Path(path)
        if path.exists() and path.is_file():
            try:
                data = etree.parse(path, parser=etree.XMLParser())
            except Exception:
                logger.error(
                    f"Failed to parse the NFO file: {Colors.RED}%s{Colors.END}",
                    path,
                    exc_info=True,
                )

        # if data is None, return an empty MediaMeta
        meta = self.extract(data) if data else MediaMeta()
        meta.path = str(path.resolve())
        return meta

    @abstractmethod
    def extract(self, data: etree._ElementTree) -> MediaMeta:
        raise NotImplementedError

    def text(self, element: etree._Element | None, tag_name: str) -> str | None:
        """Get the text content of the first matching sub-element.

        Args:
            element: The parent XML element.
            tag_name: The tag name of the sub-element.

        Returns:
            The text content of the sub-element, or None if not found.
        """
        if element is None:
            return None
        tag = element.find(tag_name)
        # https://lxml.de/tutorial.html#elements-are-lists
        if tag is not None and tag.text:
            return tag.text.strip()
        return None

    def integer(self, element: etree._Element | None, tag_name: str) -> int | None:
        """Get the integer content of the first matching sub-element.

        Args:
            element: The parent XML element.
            tag_name: The tag name of the sub-element.

        Returns:
            The integer content of the sub-element, or None if not found or invalid.
        """
        text = self.text(element, tag_name)
        if text and text.isdigit():
            return int(text)
        return None

    def decimal(self, element: etree._Element | None, tag_name: str) -> Decimal | None:
        """Get the decimal content of the first matching sub-element.

        Args:
            element: The parent XML element.
            tag_name: The tag name of the sub-element.

        Returns:
            The decimal content of the sub-element, or None if not found or invalid.
        """
        text = self.text(element, tag_name)
        if text:
            try:
                return Decimal(text)
            except Exception:
                logger.warning("Invalid decimal value for tag '%s': %s", tag_name, text)
        return None


_PARSERS: dict[LibType, NFOParser] = {}


def get_parser(lib_type: LibType) -> NFOParser:
    """Get the registered parser for the given type.

    Args:
        lib_type: The media library type.

    Raises:
        ValueError: If the type is not supported.

    Returns:
        The registered parser for the type.
    """
    parser = _PARSERS.get(lib_type)
    if parser is None:
        raise ValueError(f"Unsupported media library type: {lib_type}")
    return parser
