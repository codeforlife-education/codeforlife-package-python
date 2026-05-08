"""
© Ocado Group
Created on 19/01/2026 at 09:56:31(+00:00).
"""

import typing as t

from django.db import models

from ..tests import ModelTestCase
from ..user.models import OtpBypassToken
from .encrypted import EncryptedModel
from .fields import EncryptedTextField

if t.TYPE_CHECKING:
    from django_stubs_ext.db.models import TypedModelMeta
else:
    TypedModelMeta = object

# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods


# pylint: disable-next=abstract-method
class Person(EncryptedModel):
    associated_data = "person"

    name = EncryptedTextField(associated_data="name")

    class Meta(TypedModelMeta):
        app_label = "codeforlife.user"


class TestEncryptedModel(ModelTestCase[EncryptedModel]):
    def test_objects___update__cannot_update(self):
        """Cannot update encrypted field via objects.update()."""
        with self.assert_raises_validation_error(code="cannot_update"):
            Person.objects.update(name="Alice")

    def test_objects___bulk_update(self):
        """Cannot bulk update encrypted field via objects.bulk_update()."""
        assert Person.objects.bulk_update is None

    def test_objects___abulk_update(self):
        """Cannot abulk_update encrypted field via objects.abulk_update()."""
        assert Person.objects.abulk_update is None

    def test_objects___bulk_create(self):
        """Cannot bulk create encrypted field via objects.bulk_create()."""
        assert Person.objects.bulk_create is None

    def test_objects___abulk_create(self):
        """Cannot abulk_create encrypted field via objects.abulk_create()."""
        assert Person.objects.abulk_create is None

    def test_objects__in_bulk(self):
        """Cannot in_bulk encrypted field via objects.in_bulk()."""
        assert Person.objects.in_bulk is None

    def test_objects__ain_bulk(self):
        """Cannot ain_bulk encrypted field via objects.ain_bulk()."""
        assert Person.objects.ain_bulk is None

    def test_dek_aead(self):
        """dek_aead raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            # pylint: disable-next=expression-not-assigned
            Person().dek_aead

    def test_check__e001(self):
        """Check for missing associated_data."""

        # pylint: disable-next=abstract-method
        class EncryptedE001(EncryptedModel):
            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(error_id="encrypted.E001", model_class=EncryptedE001)

    def test_check__e002(self):
        """Check for string associated_data."""

        # pylint: disable-next=abstract-method
        class EncryptedE002(EncryptedModel):
            associated_data = 123  # type: ignore[assignment]

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(error_id="encrypted.E002", model_class=EncryptedE002)

    def test_check__e003(self):
        """Check for non-empty associated_data."""

        # pylint: disable-next=abstract-method
        class EncryptedE003(EncryptedModel):
            associated_data = ""

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(error_id="encrypted.E003", model_class=EncryptedE003)

    def test_check__e004(self):
        """Check for unique associated_data."""

        # pylint: disable-next=abstract-method
        class EncryptedE004(EncryptedModel):
            associated_data = OtpBypassToken.associated_data

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(error_id="encrypted.E004", model_class=EncryptedE004)

    def test_check__e005(self):
        """Check manager subclasses EncryptedModel.Manager."""

        # pylint: disable-next=abstract-method
        class EncryptedE005(EncryptedModel):
            associated_data = "example"

            objects = models.Manager()  # type: ignore[assignment]

            class Meta(TypedModelMeta):
                app_label = "codeforlife.user"

        self.assert_check(error_id="encrypted.E005", model_class=EncryptedE005)
