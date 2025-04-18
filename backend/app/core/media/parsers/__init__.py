from app.core.media.parsers.base import NFOParser
from app.utils.importer import import_subclasses

# import all NFO parsers in the current directory
import_subclasses(NFOParser, globals())
