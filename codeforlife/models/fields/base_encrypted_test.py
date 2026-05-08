"""
© Ocado Group
Created on 19/01/2026 at 09:56:57(+00:00).
"""

import typing as t
from functools import cached_property
from unittest.mock import MagicMock

from django.db import models

from ...encryption import FakeAead, create_dek, get_dek_aead
from ...tests import InterruptPipelineError, TestCase
from ..encrypted import EncryptedModel
from .base_encrypted import BaseEncryptedField

if t.TYPE_CHECKING:
    from django_stubs_ext.db.models import TypedModelMeta
else:
    TypedModelMeta = object

# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
# pylint: disable=protected-access


class FakeEncryptedModel(EncryptedModel):
    """A fake EncryptedModel without fields for testing."""

    associated_data = "model"

    class Meta(TypedModelMeta):
        abstract = True

    @cached_property
    def dek_aead(self):
        return t.cast(FakeAead, get_dek_aead(create_dek())).as_mock()

    def get_pending_encryption_value(self, field: BaseEncryptedField) -> str:
        """Gets the pending encryption value for the given field."""
        assert field in self.ENCRYPTED_FIELDS
        return self.__pending_encryption_values__[field.attname]

    def set_pending_encryption_value(
        self, field: BaseEncryptedField, value: str
    ):
        """Sets the pending encryption value for the given field."""
        assert field in self.ENCRYPTED_FIELDS
        self.__pending_encryption_values__[field.attname] = value

    def assert_pending_encryption_value_is_cached(
        self, field: BaseEncryptedField, value: str
    ):
        """Asserts the value for the given field is cached."""
        assert field.attname in self.__pending_encryption_values__
        assert self.__pending_encryption_values__[field.attname] == value

    def assert_pending_encryption_value_is_not_cached(
        self, field: BaseEncryptedField
    ):
        """Asserts the value for the given field is not cached."""
        assert field.attname not in self.__pending_encryption_values__

    def get_decrypted_value(self, field: BaseEncryptedField) -> str:
        """Gets the decrypted value for the given field."""
        assert field in self.ENCRYPTED_FIELDS
        return self.__decrypted_values__[field.attname]

    def set_decrypted_value(self, field: BaseEncryptedField, value: str):
        """Sets the decrypted value for the given field."""
        assert field in self.ENCRYPTED_FIELDS
        self.__decrypted_values__[field.attname] = value

    def assert_decrypted_value_is_cached(
        self, field: BaseEncryptedField, value: str
    ):
        """Asserts the value for the given field is cached."""
        assert field.attname in self.__decrypted_values__
        assert self.__decrypted_values__[field.attname] == value

    def assert_decrypted_value_is_not_cached(self, field: BaseEncryptedField):
        """Asserts the value for the given field is not cached."""
        assert field.attname not in self.__decrypted_values__


class FakeModelMeta(TypedModelMeta):
    """A fake Meta class for testing."""

    app_label = "codeforlife.user"


# pylint: disable-next=abstract-method
class FakeEncryptedField(BaseEncryptedField[str]):
    """A fake BaseEncryptedField for testing."""

    value_to_bytes: MagicMock
    bytes_to_value: MagicMock
    _encrypt: MagicMock
    _decrypt: MagicMock

    @staticmethod
    def _value_to_bytes(value: str):
        return value.encode()

    @staticmethod
    def _bytes_to_value(data: bytes):
        return data.decode()

    def __init__(self, associated_data, **kwargs):
        super().__init__(associated_data, **kwargs)

        self.value_to_bytes = MagicMock(side_effect=self._value_to_bytes)
        self.bytes_to_value = MagicMock(side_effect=self._bytes_to_value)
        self._encrypt = MagicMock(side_effect=super()._encrypt)
        self._decrypt = MagicMock(side_effect=super()._decrypt)


# pylint: disable-next=too-many-public-methods
class TestBaseEncryptedField(TestCase):
    # --------------------------------------------------------------------------
    # Test Helper Methods
    # --------------------------------------------------------------------------

    def _get_model_class(self):
        """Dynamically creates a FakeEncryptedModel subclass with fields.

        This assigns self.field and self.field2 to the model.
        """

        class Model(FakeEncryptedModel):
            """A fake EncryptedModel with fields for testing."""

            field = self.field
            field2 = self.field2

            Meta = FakeModelMeta

        return Model

    def _get_model_instance(self, **kwargs):
        """Gets an instance of the dynamically created model class."""
        return self._get_model_class()(**kwargs)

    def setUp(self):
        # Set up the first field with a non-callable default for testing.
        self.field_associated_data = "field"
        self.field = FakeEncryptedField(
            associated_data=self.field_associated_data
        )

        # Set up a second field with a callable default for testing.
        self.field2_associated_data = "field2"
        self.field2 = FakeEncryptedField(
            associated_data=self.field2_associated_data
        )

    # --------------------------------------------------------------------------
    # Construction & Deconstruction Tests
    # --------------------------------------------------------------------------

    def test_init__no_associated_data(self):
        """Cannot create BaseEncryptedField with no associated data."""
        with self.assert_raises_validation_error(code="no_associated_data"):
            BaseEncryptedField(associated_data="")

    def test_init(self):
        """BaseEncryptedField is constructed correctly."""
        assert self.field.associated_data == self.field_associated_data

    def test_deconstruct(self):
        """BaseEncryptedField is deconstructed correctly."""
        _, _, _, kwargs = self.field.deconstruct()

        assert kwargs["associated_data"] == self.field_associated_data

    # --------------------------------------------------------------------------
    # Django Model Field Integration Tests
    # --------------------------------------------------------------------------

    def test_contribute_to_class__invalid_model_base_class(self):
        """Cannot contribute BaseEncryptedField to invalid model base class."""
        with self.assert_raises_validation_error(
            code="invalid_model_base_class"
        ):
            # pylint: disable-next=unused-variable
            class Model(models.Model):
                field = self.field

                Meta = FakeModelMeta

    def test_contribute_to_class__already_registered(self):
        """Cannot contribute BaseEncryptedField that is already registered."""
        with self.assert_raises_validation_error(code="already_registered"):
            # pylint: disable-next=unused-variable
            class Model(FakeEncryptedModel):
                field = self.field
                field2 = self.field

                Meta = FakeModelMeta

    def test_contribute_to_class(self):
        """BaseEncryptedField is contributed to class correctly."""
        Model = self._get_model_class()  # Assign fields to model.
        self.assertListEqual(Model.ENCRYPTED_FIELDS, [self.field, self.field2])

    def test_contribute_to_class__associated_data_already_used(self):
        """
        Cannot contribute BaseEncryptedField with duplicate associated data.
        """
        with self.assert_raises_validation_error(
            code="associated_data_already_used"
        ):
            # pylint: disable-next=unused-variable
            class Model(FakeEncryptedModel):
                field = self.field
                field2 = FakeEncryptedField(
                    associated_data=self.field_associated_data
                )

                Meta = FakeModelMeta

    # --------------------------------------------------------------------------
    # Encryption & Decryption Tests
    # --------------------------------------------------------------------------

    def test_bytes_to_value(self):
        """bytes_to_value raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            # pylint: disable-next=expression-not-assigned
            BaseEncryptedField[str](associated_data="test").bytes_to_value(
                b"data"
            )

    def test_value_to_bytes(self):
        """value_to_bytes raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            # pylint: disable-next=expression-not-assigned
            BaseEncryptedField[str](associated_data="test").value_to_bytes(
                "value"
            )

    def test_full_associated_data(self):
        """Returns fully qualified associated data."""
        Model = self._get_model_class()
        assert (
            self.field.full_associated_data
            == f"{Model.associated_data}:{self.field_associated_data}".encode()
        )

    def test_decrypt_value(self):
        """decrypt_value decrypts the given ciphertext."""
        # Create instance and mock shorthands.
        instance = self._get_model_instance()
        decrypt_mock: MagicMock = instance.dek_aead.decrypt
        bytes_to_value_mock: MagicMock = self.field.bytes_to_value

        # When ciphertext is provided, decryption occurs.
        ciphertext = instance.dek_aead.encrypt(
            b"value", associated_data=self.field.full_associated_data
        )
        decrypted_value = self.field._decrypt(instance, ciphertext)
        decrypt_kwargs = {
            "ciphertext": ciphertext,
            "associated_data": self.field.full_associated_data,
        }
        decrypt_mock.assert_called_once_with(**decrypt_kwargs)
        decrypted_bytes = decrypt_mock.side_effect(**decrypt_kwargs)
        bytes_to_value_mock.assert_called_once_with(decrypted_bytes)
        assert decrypted_value == bytes_to_value_mock.side_effect(
            decrypted_bytes
        )

    def test__encrypt(self):
        """_encrypt encrypts the given plaintext."""
        # Create instance and mock shorthands.
        instance = self._get_model_instance()
        encrypt_mock: MagicMock = instance.dek_aead.encrypt
        value_to_bytes_mock: MagicMock = self.field.value_to_bytes

        # When plaintext is provided, encryption occurs.
        plaintext = "some value"
        encrypted_bytes = self.field._encrypt(instance, plaintext)
        value_to_bytes_mock.assert_called_once_with(plaintext)
        decrypted_bytes = value_to_bytes_mock.side_effect(plaintext)
        encrypt_kwargs = {
            "plaintext": decrypted_bytes,
            "associated_data": self.field.full_associated_data,
        }
        encrypt_mock.assert_called_once_with(**encrypt_kwargs)
        assert self.field._decrypt(instance, encrypted_bytes) == plaintext

    def test_get__descriptor(self):
        """Getting field from class returns the descriptor."""
        Model = self._get_model_class()
        assert isinstance(Model.field, BaseEncryptedField.descriptor_class)
        assert Model.field.field == self.field

    def test_set__none(self):
        """Setting field to None stores None."""
        instance = self._get_model_instance()
        assert instance.field == b""
        instance.set_decrypted_value(self.field, "decrypted value")

        FakeEncryptedField.set(instance, None, "field")
        assert instance.field is None
        instance.assert_decrypted_value_is_not_cached(self.field)
        instance.assert_pending_encryption_value_is_not_cached(self.field)

    def test_set__value(self):
        """Setting field to a valid value stores it as pending encryption."""
        instance = self._get_model_instance()
        assert instance.field == b""
        instance.set_decrypted_value(self.field, "decrypted value")

        value = "value"
        FakeEncryptedField.set(instance, value, "field")
        assert instance.field is None
        instance.assert_decrypted_value_is_not_cached(self.field)
        instance.assert_pending_encryption_value_is_cached(self.field, value)

        self.field._decrypt.assert_not_called()

    def test_get__pending_encryption(self):
        """
        Getting a field that's pending encryption returns the pending value.
        """
        value = "pending value"
        instance = self._get_model_instance()
        instance.set_pending_encryption_value(self.field, value)

        assert FakeEncryptedField.get(instance, "field") == value

    def test_get__decrypted(self):
        """
        Getting a field that's already decrypted returns the decrypted value.
        """
        value = "decrypted value"
        instance = self._get_model_instance()
        instance.set_decrypted_value(self.field, value)

        assert FakeEncryptedField.get(instance, "field") == value

        self.field._decrypt.assert_not_called()

    def test_get__none(self):
        """Getting a field when stored value is None returns None."""
        instance = self._get_model_instance(field=None)
        assert FakeEncryptedField.get(instance, "field") is None

        self.field._decrypt.assert_not_called()

    def test_get__encrypted(self):
        """
        Getting a field with stored ciphertext decrypts, caches and returns
        the value.
        """
        plaintext = "decrypted_value"

        # Create instance with stored ciphertext.
        instance = self._get_model_instance()
        ciphertext = instance.dek_aead.encrypt(
            plaintext.encode(), self.field.full_associated_data
        )
        instance.field = ciphertext

        # Get the field value, which should decrypt the ciphertext.
        instance.assert_decrypted_value_is_not_cached(self.field)
        assert FakeEncryptedField.get(instance, "field") == plaintext
        instance.assert_decrypted_value_is_cached(self.field, plaintext)

        self.field._decrypt.assert_called_once_with(instance, ciphertext)

    # --------------------------------------------------------------------------
    # pre_save Tests
    # --------------------------------------------------------------------------

    def test_pre_save__pending_encryption(self):
        """pre_save encrypts pending encryption before saving."""
        # Create instance with pending encryption.
        value = "pending value"
        instance = self._get_model_instance()
        instance.set_pending_encryption_value(self.field, value)

        # Assert the value is encrypted in pre_save.
        def assert_pre_save(result):
            self.field._encrypt.assert_called_once_with(instance, value)
            assert result != value
            assert self.field._decrypt.side_effect(instance, result) == value

        # Run the save pipeline, interrupting at pre_save.
        InterruptPipelineError.run(
            test_case=self,
            step_target=self.field,
            step_attribute="pre_save",
            assert_step=assert_pre_save,
            pipeline=instance.save,
        )

    def test_pre_save__none(self):
        """pre_save with no value does nothing."""
        # Create instance with no stored value.
        instance = self._get_model_instance(field=None)

        # Assert pre_save does nothing.
        def assert_pre_save(result):
            assert result is None
            self.field._encrypt.assert_not_called()

        # Run the save pipeline, interrupting at pre_save.
        InterruptPipelineError.run(
            test_case=self,
            step_target=self.field,
            step_attribute="pre_save",
            assert_step=assert_pre_save,
            pipeline=instance.save,
        )

    def test_pre_save__ciphertext(self):
        """pre_save with ciphertext does nothing."""
        # Create instance with ciphertext.
        ciphertext = b"encrypted_value"
        instance = self._get_model_instance(field=ciphertext)

        # Assert pre_save returns the ciphertext directly.
        def assert_pre_save(result):
            assert result == ciphertext
            self.field._encrypt.assert_not_called()

        # Run the save pipeline, interrupting at pre_save.
        InterruptPipelineError.run(
            test_case=self,
            step_target=self.field,
            step_attribute="pre_save",
            assert_step=assert_pre_save,
            pipeline=instance.save,
        )
