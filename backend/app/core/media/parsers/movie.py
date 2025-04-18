from lxml import etree

from app.core.media.parsers.base import _PARSERS, MediaMeta, NFOParser
from app.models.media import LibType


class MovieNFOParser(NFOParser):
    """The NFO parser for movie library type."""

    def extract(self, data: etree._ElementTree) -> MediaMeta:
        """Extract the metadata for a movie.

        Args:
            data: The XML data to extract from.

        Returns:
            The extracted metadata.
        """
        meta = MediaMeta()
        movie = data.getroot()
        meta.title = self.text(movie, "title")
        meta.year = self.integer(movie, "year")
        meta.rating = self.decimal(movie, "rating")
        art = movie.find("art")
        meta.cover = self.text(art, "poster")
        meta.backdrop = self.text(art, "fanart")
        return meta


_PARSERS[LibType.MOVIE] = MovieNFOParser()
