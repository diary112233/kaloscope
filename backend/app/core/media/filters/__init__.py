from app.core.media.filters.base import EventFilter
from app.utils.importer import import_subclasses

# import all event filters in the current directory
import_subclasses(EventFilter, globals())
