"""
© Ocado Group
Created on 19/01/2024 at 15:18:48(+00:00).

Base model for all Django models.

Supports optional `field_aliases` expansion during `save(update_fields=...)`.
When an alias is present in `update_fields`, it is replaced by its mapped real
field names so property-driven transformations can persist all dependent
columns in a single save.
"""

import typing as t

from django.db import models

if t.TYPE_CHECKING:
    from django.db.models.base import ModelBase
    from django_stubs_ext.db.models import TypedModelMeta
else:
    TypedModelMeta = object


class Model(models.Model):
    """Base for all models."""

    field_aliases: t.Dict[str, t.Set[str]]
    objects: models.Manager[t.Self]

    class Meta(TypedModelMeta):
        abstract = True

    def save(
        self,
        *args,
        force_insert: t.Union[bool, t.Tuple["ModelBase", ...]] = False,
        force_update: bool = False,
        using: t.Optional[str] = None,
        update_fields: t.Optional[t.Iterable[str]] = None
    ):
        """Save the model, expanding any field aliases in `update_fields`."""
        if update_fields:
            new_update_fields = set(update_fields)
            # Replace any fields in update_fields with their aliased fields.
            for field in update_fields:
                if field in self.field_aliases:
                    new_update_fields.remove(field)
                    new_update_fields.update(self.field_aliases[field])
            update_fields = new_update_fields

        super().save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


AnyModel = t.TypeVar("AnyModel", bound=Model)
