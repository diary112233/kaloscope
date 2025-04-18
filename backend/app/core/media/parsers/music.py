from lxml import etree

from app.core.media.parsers.base import _PARSERS, MediaMeta, NFOParser
from app.models.media import LibType


class MusicNFOParser(NFOParser):
    """The NFO parser for music library type."""

    def extract(self, data: etree._ElementTree) -> MediaMeta:
        """Extract the metadata for a music item.

        Args:
            data: The XML data to extract from.

        Returns:
            The extracted metadata.
        """
        return MediaMeta()


_PARSERS[LibType.MUSIC] = MusicNFOParser()
