"""
© Ocado Group
Created on 18/05/2026 at 15:38:05(+01:00).
"""

import typing as t

from django.db.models import Field, Model

AnyModel = t.TypeVar("AnyModel", bound=Model)
T = t.TypeVar("T")
Normalize: t.TypeAlias = t.Callable[[T], T]


class NormalizedField(Field, t.Generic[AnyModel, T]):
    """A Django model field that normalizes values before saving."""

    def __init__(self, normalize: None | Normalize[T], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.normalize = normalize

    @classmethod
    def set(
        cls, instance: AnyModel, value: None | T, field_name: str, **kwargs
    ):
        """
        Normalize and assign a value to a NormalizedField.

        Args:
            instance: The model instance on which to set the value.
            value: The value to normalize and set.
            field_name: The name of the NormalizedField on the model.
        """
        if value is not None:
            field = t.cast(
                NormalizedField[AnyModel, T],
                instance._meta.get_field(field_name),
            )
            if field.normalize is not None:
                value = field.normalize(value)

        setattr(instance, field_name, value)
