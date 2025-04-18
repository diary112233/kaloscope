from app.core.media.filters.base import _FILTERS, EventFilter
from app.models.media import LibType


class MusicEventFilter(EventFilter):
    """The event filter for music library type."""

    def accept(self) -> list[str]:
        """The mime types accepted by the music library type.

        Returns:
            The list of mime types.
        """
        return ["audio/*"]

    def hierarchies(self) -> list[int]:
        """The hierarchy levels for the music library type.

        Music
        ├── Some Artist
        │   ├── Album A
        │   │   ├── Song 1.flac
        │   │   ├── Song 2.flac
        │   │   └── Song 3.flac
        │   └── Album B
        │       ├── Track 1.m4a
        │       ├── Track 2.m4a
        │       └── Track 3.m4a
        └── Album X
            ├── Whatever You.mp3
            ├── Like To.mp3
            ├── Name Your.mp3
            └── Music Files.mp3

        Returns:
            The list of hierarchy levels.
        """
        return [2, 3]


_FILTERS[LibType.MUSIC] = MusicEventFilter()
