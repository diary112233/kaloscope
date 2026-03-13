from lxml import etree

from app.core.media.handlers.base import _HANDLERS, MediaHandler, MediaMeta
from app.models.media import LibType


class MovieMediaHandler(MediaHandler):
    """The media item handler for movie library type."""

    def accept(self) -> list[str]:
        """The mime types accepted by the movie library type.

        Returns:
            The list of mime types.
        """
        return ["video/*"]

    def hierarchies(self) -> list[int]:
        """The hierarchy levels for the movie library type.

        Movies
        ├── Film (1990).mp4
        ├── Film (1994).mp4
        ├── Film (2008)
        │   └── Film.mkv
        └── Film (2010)
            ├── Film-cd1.avi
            └── Film-cd2.avi

        Returns:
            The list of hierarchy levels.
        """
        return [1, 2]

    def extract_meta(self, data: etree._ElementTree) -> MediaMeta:
        """Extract the metadata for a movie.

        Args:
            data: The XML data to extract from.

        Returns:
            The extracted metadata.
        """
        meta = MediaMeta()
        movie = data.getroot()
        meta.title = self.get_text(movie, "title")
        meta.year = self.get_integer(movie, "year")
        art = movie.find("art")
        meta.cover = self.get_text(art, "poster")
        meta.backdrop = self.get_text(art, "fanart")
        meta.rating = self.get_decimal(movie, "rating")
        return meta


_HANDLERS[LibType.MOVIE] = MovieMediaHandler()
