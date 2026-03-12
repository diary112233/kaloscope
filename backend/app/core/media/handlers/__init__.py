from app.core.media.handlers.base import MediaHandler
from app.utils.importer import import_subclasses

# import all media item handlers in the current directory
import_subclasses(MediaHandler, globals())
