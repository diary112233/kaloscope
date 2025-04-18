from tortoise.fields import BooleanField, CharField, IntField, TextField

from app.models.base import TortoiseModel


# -------------------- ORM Models -------------------- #
class GlobalVariable(TortoiseModel):
    key = CharField(max_length=64, unique=True)
    value = CharField(max_length=255)
    value_length = IntField()
    encrypted = BooleanField()

    class Meta:
        table = "global_variable"
        ordering = ["-created_at"]


class GlobalCookie(TortoiseModel):
    name = TextField()
    value = TextField()
    domain = TextField()
    path = TextField()
    expires = IntField(null=True)

    class Meta:
        table = "global_cookie"
        unique_together = (("name", "domain", "path"),)
