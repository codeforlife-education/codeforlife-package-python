"""
© Ocado Group
Created on 19/01/2026 at 09:57:04(+00:00).

This module contains the core field-level logic for transparent encryption and
decryption.

`BaseEncryptedField` stores ciphertext in the model field (bytes/memoryview)
and exposes static convenience methods, `get()` and `set()`, to work with
typed plaintext values.

- `set(instance, value, field_name)` stores plaintext in
    `instance.__pending_encryption_values__`.
- `pre_save()` encrypts pending plaintext and writes ciphertext to the DB.
- `get(instance, field_name)` returns plaintext by reading pending data,
    returning a cached decrypted value, or decrypting stored ciphertext.

The descriptor class remains intentionally minimal: it only clears cached
decrypted values when the underlying binary value changes. It does not perform
type conversion or wrapper-based state transitions.
"""

import typing as t

from django.core.exceptions import ValidationError
from django.db.models import BinaryField

from ...types import Args, KwArgs
from ..encrypted import EncryptedModel
from ..utils import is_real_model_class
from .deferred_attribute import DeferredAttribute
from .normalized import Normalize, NormalizedField

T = t.TypeVar("T")
Ciphertext: t.TypeAlias = t.Union[bytes, memoryview]
AnyBaseEncryptedField = t.TypeVar(
    "AnyBaseEncryptedField", bound="BaseEncryptedField"
)


class EncryptedAttribute(
    DeferredAttribute[AnyBaseEncryptedField, EncryptedModel, Ciphertext],
    t.Generic[AnyBaseEncryptedField],
):
    """Descriptor that clears cached decrypted values on assignment."""

    def __set__(self, instance, value):
        # Clear any cached decrypted value.
        instance.__decrypted_values__.pop(self.field.attname, None)

        # Set the internal value on the instance.
        super().__set__(instance, value)


class BaseEncryptedField(
    NormalizedField[EncryptedModel, T], BinaryField, t.Generic[T]
):
    """Binary field base class for storing encrypted typed values."""

    model: t.Type[EncryptedModel]

    descriptor_class = EncryptedAttribute

    def __init__(
        self,
        associated_data: str,
        normalize: None | Normalize[T] = None,
        unique: t.Literal[False] = False,
        **kwargs,
    ):
        if unique:
            raise ValidationError(
                f"{self.__class__.__name__} does not support unique=True.",
                code="unique_not_supported",
            )
        if not associated_data:
            raise ValidationError(
                "Associated data cannot be empty.",
                code="no_associated_data",
            )
        self.associated_data = associated_data

        super().__init__(normalize=normalize, unique=unique, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = t.cast(
            t.Tuple[str, str, Args, KwArgs], super().deconstruct()
        )

        kwargs["associated_data"] = self.associated_data

        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, private_only=False):
        """
        Called by Django when the field is added to a model. This method
        performs critical validations and registers the field with the model.
        """
        super().contribute_to_class(cls, name, private_only)

        # Skip non-real models.
        if not is_real_model_class(cls):
            return

        # Ensure the model subclasses EncryptedModel.
        if not issubclass(cls, EncryptedModel):
            raise ValidationError(
                f"'{cls.__module__}.{cls.__name__}' must subclass"
                f" '{EncryptedModel.__module__}.{EncryptedModel.__name__}'.",
                code="invalid_model_base_class",
            )

        # Ensure no duplicate encrypted fields.
        if self in cls.ENCRYPTED_FIELDS:
            raise ValidationError(
                "Encrypted field already registered.",
                code="already_registered",
            )

        # Ensure no duplicate associated data.
        for field in cls.ENCRYPTED_FIELDS:
            if self.associated_data == field.associated_data:
                raise ValidationError(
                    f"The encrypted fields '{self.name}' and '{field.name}'"
                    " have the same associated data.",
                    code="associated_data_already_used",
                )

        # Register this field as an encrypted field on the model.
        cls.ENCRYPTED_FIELDS.append(self)

    @t.overload  # type: ignore[override]
    def __get__(  # Get the descriptor.
        self, instance: None, owner: t.Any
    ) -> EncryptedAttribute[t.Self]: ...

    @t.overload
    def __get__(  # Get the value.
        self, instance: EncryptedModel, owner: t.Any
    ) -> t.Optional[Ciphertext]: ...

    # Actual implementation of __get__.
    def __get__(self, instance: t.Optional[EncryptedModel], owner: t.Any):
        return t.cast(
            t.Union[EncryptedAttribute[t.Self], t.Optional[Ciphertext]],
            # pylint: disable-next=no-member
            super().__get__(instance, owner),
        )

    def __set__(  # Set the value.
        self, instance: EncryptedModel, value: t.Optional[Ciphertext]
    ): ...

    def value_from_object(self, obj):
        return t.cast(t.Optional[Ciphertext], super().value_from_object(obj))

    def pre_save(
        self, model_instance: EncryptedModel, add  # type: ignore[override]
    ):
        """Encrypt pending plaintext values before writing to the database."""

        # Data needs encrypting.
        if self.attname in model_instance.__pending_encryption_values__:
            value = t.cast(
                T,
                model_instance.__pending_encryption_values__.pop(self.attname),
            )
            encrypted_value = self._encrypt(model_instance, value)

            model_instance.__decrypted_values__[self.attname] = value
            model_instance.__dict__[self.attname] = encrypted_value

            return encrypted_value

        # If data is already encrypted or None, return it as-is.
        return super().pre_save(model_instance, add)

    def bytes_to_value(self, data: bytes) -> T:
        """
        Subclasses must implement this method to convert decrypted bytes back to
        the field's value type.
        """
        raise NotImplementedError()

    def value_to_bytes(self, value: T) -> bytes:
        """
        Subclasses must implement this method to convert the field's value to
        bytes before encryption.
        """
        raise NotImplementedError()

    @property
    def full_associated_data(self):
        """Returns the fully qualified associated data for this field."""
        return f"{self.model.associated_data}:{self.associated_data}".encode()

    def _decrypt(self, instance: EncryptedModel, ciphertext: bytes):
        """Decrypts a single value using the DEK and associated data."""
        data = (
            b""
            if ciphertext == b""
            else instance.dek_aead.decrypt(
                ciphertext=ciphertext,
                associated_data=self.full_associated_data,
            )
        )

        return self.bytes_to_value(data)

    def _encrypt(self, instance: EncryptedModel, value: T):
        """Encrypts a single value using the DEK and associated data."""
        plaintext = self.value_to_bytes(value)

        return (
            b""
            if plaintext == b""
            else instance.dek_aead.encrypt(
                plaintext=plaintext,
                associated_data=self.full_associated_data,
            )
        )

    @staticmethod
    def get(instance: EncryptedModel, field_name: str):
        """Get a typed plaintext value for an encrypted field.

        Args:
            instance: The model instance from which to decrypt the value.
            field_name: The name of the encrypted field to decrypt.

        Returns:
            The plaintext value, or None if the field is empty.

        Notes:
            Internal model storage remains ciphertext bytes. This helper applies
            the conversion/decryption path and cache handling.
        """
        field = t.cast(
            BaseEncryptedField[T], instance._meta.get_field(field_name)
        )

        # If we have a cached pending encryption value, return it.
        if field.attname in instance.__pending_encryption_values__:
            return t.cast(
                T, instance.__pending_encryption_values__[field.attname]
            )

        # If we have a cached decrypted value, return it.
        if field.attname in instance.__decrypted_values__:
            return t.cast(T, instance.__decrypted_values__[field.attname])

        # Get the internal value from the instance's __dict__.
        value = field.value_from_object(instance)
        if value is None:
            return None

        # Decrypt the value before returning it.
        # pylint: disable-next=protected-access
        decrypted_value = field._decrypt(instance, bytes(value))

        # Cache the decrypted value on the instance.
        instance.__decrypted_values__[field.attname] = decrypted_value

        return decrypted_value

    @classmethod
    def set(cls, instance, value, field_name, **kwargs):
        """Set a typed plaintext value for an encrypted field.

        The plaintext is staged in pending-encryption storage and encrypted at
        save time by `pre_save`.

        Args:
            instance: The model instance on which to set the value.
            value: The plaintext value to set. If None, the field is cleared.
            field_name: The name of the encrypted field to set.
            normalize: Whether to normalize the value before setting it.
        """
        field = t.cast(
            BaseEncryptedField[T], instance._meta.get_field(field_name)
        )

        # Set the pending encryption value.
        if value is None:
            instance.__pending_encryption_values__.pop(field.attname, None)
        else:
            if kwargs.get("normalize", True) and field.normalize is not None:
                value = field.normalize(value)
            instance.__pending_encryption_values__[field.attname] = value

        # In all cases we need to clear the internal and cached-decrypted value.
        setattr(instance, field_name, None)
