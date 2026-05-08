"""
© Ocado Group
Created on 19/01/2026 at 09:56:25(+00:00).

This is the base class for any model that will contain encrypted fields. Its
primary role is to override the default manager to disable bulk operations that
could otherwise bypass the field-level encryption logic, potentially leading to
data corruption or leaks. It also uses Django's `check` framework to validate
the model's configuration.

A critical security measure in this architecture is the custom `Manager` within
`EncryptedModel`. Standard Django bulk operations like `bulk_create()` and
`update()` bypass the individual model's `save()` method and, by extension, our
custom field's `pre_save` logic. If these methods were allowed, it would be
possible to insert or update data without it being properly encrypted, or to
corrupt existing encrypted data.

To prevent this, the `Manager` explicitly disables these operations by setting
them to `None`. The `update()` method is given a special implementation that
actively checks if any of the fields being updated are encrypted fields and
raises a `ValidationError` if they are. This forces developers to fetch model
instances and update their properties individually, ensuring the encryption
logic is always triggered. Furthermore, the model's `check` framework includes a
validation step to ensure that any subclass of `EncryptedModel` is using a
manager that inherits from `EncryptedModel.Manager`, guaranteeing these security
measures are always enforced.
"""

import typing as t

from django.apps import apps
from django.core import checks
from django.core.exceptions import ValidationError
from django.db import models

from .base import Model
from .utils import is_real_model_class

if t.TYPE_CHECKING:
    from django_stubs_ext.db.models import TypedModelMeta
    from tink.aead import Aead  # type: ignore[import]

    from .fields import BaseEncryptedField
else:
    TypedModelMeta = object


AnyEncryptedModel = t.TypeVar("AnyEncryptedModel", bound="EncryptedModel")


class EncryptedModel(Model):
    """Base for all models with encrypted fields."""

    associated_data: str

    ENCRYPTED_FIELDS: t.List["BaseEncryptedField"]

    def __init__(self, *args, **kwargs):
        # Each instance gets its own dict of pending-encryption and decrypted
        # values.
        self.__pending_encryption_values__: t.Dict[str, t.Any] = {}
        self.__decrypted_values__: t.Dict[str, t.Any] = {}
        super().__init__(*args, **kwargs)

    def __init_subclass__(cls):
        super().__init_subclass__()
        # Each subclass gets its own list of encrypted fields.
        cls.ENCRYPTED_FIELDS = []

    # pylint: disable-next=too-few-public-methods
    class Manager(
        models.Manager[AnyEncryptedModel], t.Generic[AnyEncryptedModel]
    ):
        """
        Base manager for models with encrypted fields. Disables bulk operations
        that would bypass field-level encryption.
        """

        def update(self, **kwargs):
            """Ensure encrypted fields are not updated via 'update()'."""
            for name in kwargs:
                if any(
                    field.name == name for field in self.model.ENCRYPTED_FIELDS
                ):
                    raise ValidationError(
                        f"Cannot update encrypted field '{name}' via"
                        " 'update()'. Set the property on each instance"
                        " instead.",
                        code="cannot_update",
                    )

            return super().update(**kwargs)

        # Disable bulk operations that would bypass field-level encryption.
        bulk_update: t.Never = None  # type: ignore[assignment]
        abulk_update: t.Never = None  # type: ignore[assignment]
        bulk_create: t.Never = None  # type: ignore[assignment]
        abulk_create: t.Never = None  # type: ignore[assignment]
        in_bulk: t.Never = None  # type: ignore[assignment]
        ain_bulk: t.Never = None  # type: ignore[assignment]

    base_manager_class: t.Type[Manager] = Manager
    objects: Manager["EncryptedModel"] = Manager()  # type: ignore[assignment]

    class Meta(TypedModelMeta):
        abstract = True

    @classmethod
    def _check_associated_data(cls):
        """
        Check 'associated_data' values are unique across all EncryptedModel
        subclasses.
        """
        errors: t.List[checks.Error] = []

        # Skip non-real models.
        if not is_real_model_class(cls):
            return errors

        # Ensure associated_data is defined.
        if not hasattr(cls, "associated_data"):
            errors.append(
                checks.Error(
                    "Must define an associated_data attribute.",
                    hint=f"{cls.__module__}.{cls.__name__}",
                    obj=cls,
                    id="encrypted.E001",
                )
            )
        # Ensure associated_data is a string.
        elif not isinstance(cls.associated_data, str):
            errors.append(
                checks.Error(
                    "associated_data must be a string.",
                    hint=f"{cls.__module__}.{cls.__name__}",
                    obj=cls,
                    id="encrypted.E002",
                )
            )
        # Ensure associated_data is not empty.
        elif not cls.associated_data:
            errors.append(
                checks.Error(
                    "associated_data cannot be empty.",
                    hint=f"{cls.__module__}.{cls.__name__}",
                    obj=cls,
                    id="encrypted.E003",
                )
            )
        # Ensure associated_data is unique.
        else:
            for model in apps.get_models():
                if (
                    # pylint: disable-next=too-many-boolean-expressions
                    not model is cls
                    and is_real_model_class(model)
                    and issubclass(model, EncryptedModel)
                    and hasattr(model, "associated_data")
                    and isinstance(model.associated_data, str)
                    and model.associated_data == cls.associated_data
                ):
                    errors.append(
                        checks.Error(
                            "Duplicate 'associated_data' detected:"
                            f" '{cls.associated_data}'",
                            hint=(
                                f"{cls.__module__}.{cls.__name__}"
                                " shares this associated data with"
                                f" {model.__module__}.{model.__name__}."
                            ),
                            obj=cls,
                            id="encrypted.E004",
                        )
                    )

        return errors

    @classmethod
    def check(cls, **kwargs):
        """Run model checks, including custom checks for encrypted models."""
        errors = super().check(**kwargs)
        errors.extend(cls._check_associated_data())

        if not issubclass(cls.objects.__class__, cls.base_manager_class):
            errors.append(
                checks.Error(
                    f"{cls.__name__} must have a manager that is a subclass of"
                    f" {cls.base_manager_class.__name__}.",
                    hint=(
                        f"Set 'objects = {cls.base_manager_class.__name__}()' "
                        f"on {cls.__module__}.{cls.__name__}."
                    ),
                    obj=cls,
                    id="encrypted.E005",
                )
            )

        return errors

    @property
    def dek_aead(self) -> "Aead":
        """Gets the AEAD primitive for this model's DEK."""
        raise NotImplementedError()
