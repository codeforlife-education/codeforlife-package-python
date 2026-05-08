"""
© Ocado Group
Created on 26/01/2026 at 13:44:31(+00:00).
"""

import typing as t
from unittest.mock import MagicMock, patch

from ..encryption import FakeAead, create_dek, get_dek_aead
from ..tests import ModelTestCase
from .base_data_encryption_key import BaseDataEncryptionKeyModel
from .fields import DataEncryptionKeyField

if t.TYPE_CHECKING:
    from django_stubs_ext.db.models import TypedModelMeta
else:
    TypedModelMeta = object

# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods


class TestDataEncryptionKeyModel(ModelTestCase[BaseDataEncryptionKeyModel]):
    @classmethod
    def get_model_class(cls):
        """
        Dynamically create a subclass of BaseDataEncryptionKeyModel for testing.
        """

        class TestModel(BaseDataEncryptionKeyModel):
            dek: DataEncryptionKeyField = DataEncryptionKeyField()

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

            def set_dek_for_test(self):
                """Sets the dek field for testing purposes."""
                self.__dict__[self.__class__.dek.field.attname] = create_dek()

        return TestModel

    def get_model_instance(self, *args, **kwargs):
        return self.get_model_class()(*args, **kwargs)

    def test_dek_aead__dek_is_none(self):
        """Raise ValidationError when dek is None on a saved instance."""
        instance = self.get_model_instance(pk=1, dek=None)
        with self.assert_raises_validation_error(code="dek_is_none"):
            _ = instance.dek_aead

    def test_dek_aead__not_cached(self):
        """Returns dek_aead and caches it when not cached."""
        # Create an instance with a primary key to mimic a saved instance.
        instance = self.get_model_instance(pk=1)
        instance.set_dek_for_test()

        # Setup the mock to return a FakeAead instance.
        dek_aead_mock = t.cast(FakeAead, get_dek_aead(instance.dek)).as_mock()
        with patch(
            "codeforlife.models.base_data_encryption_key.get_dek_aead",
            return_value=dek_aead_mock,
        ) as get_dek_aead_mock:
            # Initially, the cache should not have the dek_aead. After accessing
            # dek_aead, it should be cached.
            assert instance.pk not in instance.DEK_AEAD_CACHE
            assert instance.dek_aead is dek_aead_mock
            assert instance.pk in instance.DEK_AEAD_CACHE
            assert instance.DEK_AEAD_CACHE[instance.pk] is dek_aead_mock

            # Ensure the get_dek_aead function was called with the correct dek.
            get_dek_aead_mock.assert_called_once_with(instance.dek)

    def test_dek_aead__cached(self):
        """Returns the cached dek_aead."""
        # Create an instance with a primary key to mimic a saved instance.
        instance = self.get_model_instance(pk=1)
        instance.set_dek_for_test()

        # Pre-populate the cache with a FakeAead instance.
        dek_aead_mock = t.cast(FakeAead, get_dek_aead(instance.dek)).as_mock()
        with patch(
            "codeforlife.models.base_data_encryption_key.get_dek_aead"
        ) as get_dek_aead_mock:
            instance.DEK_AEAD_CACHE[instance.pk] = dek_aead_mock

            # Accessing dek_aead should return the cached value.
            assert instance.dek_aead is dek_aead_mock

            # Ensure the get_dek_aead function was not called as its cached.
            get_dek_aead_mock.assert_not_called()

    @patch("django.db.models.base.Model.save", autospec=True)
    @patch(
        "codeforlife.models.base_data_encryption_key.create_dek",
        autospec=True,
    )
    def test_save__creates_dek(
        self, create_dek_mock: MagicMock, save_mock: MagicMock
    ):
        """Saves a new DEK when saving a new instance."""
        instance = self.get_model_instance()
        assert instance.dek is None
        instance.save()

        # Ensure create_dek was called and save was called correctly.
        create_dek_mock.assert_called_once_with()
        save_mock.assert_called_once_with(
            instance,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
        )

        assert instance.dek is not None

    def test_check__e001(self):
        """Raises an error if the DEK field is missing."""

        class BaseDekE001(BaseDataEncryptionKeyModel):
            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(
            error_id="base_data_encryption_key.E001", model_class=BaseDekE001
        )

    def test_check__e002(self):
        """Raises an error if the DEK field is not a string."""

        class BaseDekE002(BaseDataEncryptionKeyModel):
            DEK_FIELD = 123  # type: ignore[assignment]

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(
            error_id="base_data_encryption_key.E002", model_class=BaseDekE002
        )

    def test_check__e003(self):
        """Raises an error if the DEK field name is empty."""

        class BaseDekE003(BaseDataEncryptionKeyModel):
            DEK_FIELD = ""

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(
            error_id="base_data_encryption_key.E003", model_class=BaseDekE003
        )

    def test_check__e004(self):
        """Raises an error if the DEK field does not exist on the model."""

        class BaseDekE004(BaseDataEncryptionKeyModel):
            DEK_FIELD = "non_existent_field"

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(
            error_id="base_data_encryption_key.E004", model_class=BaseDekE004
        )
