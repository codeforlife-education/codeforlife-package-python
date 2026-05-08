"""
© Ocado Group
Created on 19/01/2026 at 09:57:19(+00:00).

This field is responsible for storing the encrypted Data Encryption Key (DEK)
for a model instance. The actual lifecycle of the DEK, including its lazy
creation for new model instances, is managed by the `save()` method on the
`BaseDataEncryptionKeyModel`.

The `contribute_to_class` method on `DataEncryptionKeyField` performs crucial
validations when the field is added to a model. It ensures that the model
inherits from the correct base class (`BaseDataEncryptionKeyModel`) and, most
importantly, it guarantees that a model can only have one
`DataEncryptionKeyField`. It does this by checking a class-level `_dek`
attribute; if this attribute is already set, it means another DEK field has
already been processed, and a `ValidationError` is raised. This prevents
developers from accidentally creating multiple encryption keys for a single
model instance, which would lead to ambiguity and potential data loss.
"""

import typing as t

from django.core.exceptions import ValidationError
from django.db.models import BinaryField
from django.utils.translation import gettext_lazy as _

from ..base_data_encryption_key import BaseDataEncryptionKeyModel
from ..utils import is_real_model_class
from .deferred_attribute import DeferredAttribute

if t.TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext import StrOrPromise


AnyDataEncryptionKeyField = t.TypeVar(
    "AnyDataEncryptionKeyField", bound="DataEncryptionKeyField"
)
Dek: t.TypeAlias = t.Union[bytes, memoryview]


class DataEncryptionKeyAttribute(
    DeferredAttribute[
        AnyDataEncryptionKeyField, BaseDataEncryptionKeyModel, Dek
    ],
    t.Generic[AnyDataEncryptionKeyField],
):
    """
    Descriptor for DataEncryptionKeyField that handles data shredding.
    """

    def __set__(self, instance, value):
        # Clear any cached DEK AEAD.
        if instance.pk is not None and instance.pk in instance.DEK_AEAD_CACHE:
            instance.DEK_AEAD_CACHE.pop(instance.pk, None)

        # Set the internal value on the instance.
        super().__set__(instance, value)


class DataEncryptionKeyField(BinaryField):
    """
    A custom BinaryField to store an encrypted data encryption key (DEK).
    """

    model: t.Type[BaseDataEncryptionKeyModel]

    descriptor_class = DataEncryptionKeyAttribute

    # --------------------------------------------------------------------------
    # Construction & Deconstruction
    # --------------------------------------------------------------------------

    default_verbose_name = "data encryption key"
    default_help_text = (
        "The encrypted data encryption key (DEK) for this model."
    )

    def __init__(
        self,
        # DEK should not be editable in admin forms.
        editable: t.Literal[False] = False,
        # Allow null for data shredding.
        null: t.Literal[True] = True,
        verbose_name: t.Optional["StrOrPromise"] = _(default_verbose_name),
        help_text: "StrOrPromise" = _(default_help_text),
        **kwargs,
    ):
        if editable:
            raise ValidationError(
                "DataEncryptionKeyField cannot be editable.",
                code="editable_not_allowed",
            )
        if "default" in kwargs:
            raise ValidationError(
                "DataEncryptionKeyField cannot have a default value.",
                code="default_not_allowed",
            )
        if not null:
            raise ValidationError(
                "DataEncryptionKeyField must allow null to support data"
                " shredding.",
                code="null_not_allowed",
            )

        super().__init__(
            **kwargs,
            editable=editable,
            null=null,
            verbose_name=verbose_name,
            help_text=help_text,
        )

    # --------------------------------------------------------------------------
    # Django Model Field Integration
    # --------------------------------------------------------------------------

    def contribute_to_class(self, cls, name, private_only=False):
        super().contribute_to_class(cls, name, private_only)

        # Skip non-real models.
        if not is_real_model_class(cls):
            return

        # Ensure the model subclasses BaseDataEncryptionKeyModel.
        if not issubclass(cls, BaseDataEncryptionKeyModel):
            raise ValidationError(
                f"'{cls.__module__}.{cls.__name__}' must subclass"
                f" '{BaseDataEncryptionKeyModel.__module__}."
                f"{BaseDataEncryptionKeyModel.__name__}'.",
                code="invalid_model_base_class",
            )

        # Ensure only one DEK field per model.
        if hasattr(cls, "DEK_FIELD"):
            raise ValidationError(
                f"'{cls.__module__}.{cls.__name__}' already has a"
                " DataEncryptionKeyField defined.",
                code="multiple_dek_fields_not_allowed",
            )

        # Set the class DEK field reference.
        cls.DEK_FIELD = self.attname

    # --------------------------------------------------------------------------
    # Descriptor Methods
    # --------------------------------------------------------------------------

    @t.overload  # type: ignore[override]
    def __get__(  # Get the descriptor.
        self, instance: None, owner: t.Any
    ) -> DataEncryptionKeyAttribute[t.Self]: ...

    @t.overload
    def __get__(  # Get the value.
        self, instance: BaseDataEncryptionKeyModel, owner: t.Any
    ) -> t.Optional[bytes]: ...

    def __get__(  # Actual implementation of __get__.
        self, instance: t.Optional[BaseDataEncryptionKeyModel], owner: t.Any
    ):
        return t.cast(
            t.Union[DataEncryptionKeyAttribute[t.Self], t.Optional[bytes]],
            # pylint: disable-next=no-member
            super().__get__(instance, owner),
        )

    # Can only be set to None to allow data shredding.
    def __set__(self, instance: BaseDataEncryptionKeyModel, value: None): ...
