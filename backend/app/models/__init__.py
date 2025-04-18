from app.models.base import TortoiseModel
from app.utils.importer import import_subclasses

# import all Tortoise ORM models in the current directory
import_subclasses(TortoiseModel, globals())
