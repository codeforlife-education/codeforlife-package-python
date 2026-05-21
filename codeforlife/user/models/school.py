"""
© Ocado Group
Created on 20/02/2024 at 15:37:52(+00:00).
"""

import typing as t

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from ...models import DataEncryptionKeyModel
from ...models.fields import EncryptedTextField, Sha256Field
from ...types import Validators
from ...validators import UnicodeAlphanumericCharSetValidator

if t.TYPE_CHECKING:  # pragma: no cover
    from datetime import datetime

    from django_stubs_ext.db.models import TypedModelMeta
else:
    TypedModelMeta = object


# TODO: add to School.name field-validators in new schema.
school_name_validators: Validators = [
    UnicodeAlphanumericCharSetValidator(
        spaces=True,
        special_chars="'.",
    )
]


class SchoolModelManager(DataEncryptionKeyModel.Manager["School"]):
    """Manager for School model."""

    @classmethod
    def normalize_name(cls, name: str, lower=True):
        """Normalize a school's name.

        The value is stripped and optionally lowercased.

        Args:
            name: The name to normalize.
            lower: Whether to lowercase the name.

        Returns:
            The normalized name.
        """
        name = name.strip()
        return name.lower() if lower else name

    def get_original_queryset(self):
        """Get the original queryset without filtering."""
        return super().get_queryset()

    def get_queryset(self):
        """Filter out inactive schools by default."""
        return super().get_queryset().filter(is_active=True)


class School(DataEncryptionKeyModel):
    """A school."""

    associated_data = "school"
    field_aliases = {
        "name": {"_name_plain", "_name_enc", "_name_hash"},
    }

    # --------------------------------------------------------------------------
    # Name
    # --------------------------------------------------------------------------
    # pylint: disable=duplicate-code

    _name_hash = Sha256Field(
        verbose_name=_("name hash"),
        db_column="name_hash",
        normalize=lambda name: SchoolModelManager.normalize_name(
            name, lower=True
        ),
    )
    _name_plain: str
    _name_plain = models.CharField(  # type: ignore[assignment]
        max_length=200,
        unique=True,
    )
    _name_enc = EncryptedTextField(
        associated_data="name",
        verbose_name=_("name"),
        db_column="name_enc",
        normalize=lambda name: SchoolModelManager.normalize_name(
            name, lower=False
        ),
    )

    @property
    def name(self):
        """Get the school's name."""
        return EncryptedTextField.get(self, "_name_enc")

    @name.setter
    def name(self, value: str):
        """Set the school's name."""
        self._name_plain = SchoolModelManager.normalize_name(value, lower=False)
        EncryptedTextField.set(self, value, "_name_enc")
        Sha256Field.set(self, value, "_name_hash")

    # pylint: enable=duplicate-code
    # --------------------------------------------------------------------------

    country: t.Optional[str]
    country = CountryField(  # type: ignore[assignment]
        blank_label="(select country)",
        null=True,
        blank=True,
    )

    county: t.Optional[str]
    county = models.CharField(  # type: ignore[assignment]
        max_length=50,
        blank=True,
        null=True,
    )

    creation_time: t.Optional["datetime"]
    creation_time = models.DateTimeField(  # type: ignore[assignment]
        default=timezone.now,
        null=True,
    )

    is_active: bool
    is_active = models.BooleanField(default=True)  # type: ignore[assignment]

    objects: SchoolModelManager = (
        SchoolModelManager()  # type: ignore[assignment]
    )

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                condition=~models.Q(_name_hash=""),
                fields=["_name_hash"],
                name="unique_name_hash_non_empty",
            ),
        ]

    def __str__(self):
        return self.name

    def classes(self):
        """Get all classes associated with the school."""
        teachers = self.teacher_school.all()
        if teachers:
            classes = []
            for teacher in teachers:
                if teacher.class_teacher.all():
                    classes.extend(list(teacher.class_teacher.all()))
            return classes
        return None

    def admins(self):
        """Get all admin teachers associated with the school."""
        teachers = self.teacher_school.all()
        return (
            [teacher for teacher in teachers if teacher.is_admin]
            if teachers
            else None
        )

    def anonymise(self):
        """Anonymize the school."""
        self.dek = None
        self.is_active = False
        self.save(update_fields=["dek", "is_active"])
