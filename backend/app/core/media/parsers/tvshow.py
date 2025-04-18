from lxml import etree

from app.core.media.parsers.base import _PARSERS, MediaMeta, NFOParser
from app.models.media import LibType


class TVShowNFOParser(NFOParser):
    """The NFO parser for TV show library type."""

    def extract(self, data: etree._ElementTree) -> MediaMeta:
        """Extract the metadata for a TV show.

        Args:
            data: The XML data to extract from.

        Returns:
            The extracted metadata.
        """
        return MediaMeta()


_PARSERS[LibType.TV_SHOW] = TVShowNFOParser()
