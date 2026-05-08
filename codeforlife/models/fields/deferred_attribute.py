"""
© Ocado Group
Created on 22/01/2026 at 13:43:46(+00:00).
"""

import typing as t

from django.db.models import Field, Model
from django.db.models.query_utils import DeferredAttribute as _DeferredAttribute

AnyModel = t.TypeVar("AnyModel", bound=Model)
AnyField = t.TypeVar("AnyField", bound=Field)
T = t.TypeVar("T")


# pylint: disable-next=too-few-public-methods
class DeferredAttribute(_DeferredAttribute, t.Generic[AnyField, AnyModel, T]):
    """Custom DeferredAttribute with type hints ref to the field."""

    _field: AnyField

    @property
    def field(self):
        """Helper to get the field with the correct type."""
        # Mypy tries to be helpful here but fails to infer the correct type.
        # Hence the cast.
        return t.cast(AnyField, self._field)

    @field.setter
    def field(self, value: AnyField):
        self._field = value

    def __get__(
        self, instance: t.Optional[AnyModel], cls=None  # type: ignore[override]
    ):
        return t.cast(
            t.Union[t.Self, t.Optional[T]],
            super().__get__(instance, cls),  # type: ignore[misc]
        )

    def __set__(self, instance: AnyModel, value: t.Optional[T]):
        # Set the internal value on the instance.
        instance.__dict__[self.field.attname] = value
