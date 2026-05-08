"""
© Ocado Group
Created on 20/02/2024 at 15:41:36(+00:00).
"""

import typing as t

from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from ...types import Validators
from ...validators import AsciiNumericCharSetValidator

if t.TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext.db.models import TypedModelMeta

    from .session_auth_factor import SessionAuthFactor
    from .user import User
else:
    TypedModelMeta = object


class AuthFactor(models.Model):
    """A user's enabled authentication factor."""

    sessions: QuerySet["SessionAuthFactor"]

    otp_validators: Validators = [
        AsciiNumericCharSetValidator(),
        MinLengthValidator(6),
        MaxLengthValidator(6),
    ]

    # pylint: disable-next=too-many-ancestors
    class Type(models.TextChoices):
        """The type of authentication factor."""

        OTP = "otp", _("one-time password")

    user: "User"
    user = models.ForeignKey(  # type: ignore[assignment]
        "user.User",
        related_name="auth_factors",
        on_delete=models.CASCADE,
    )

    # NOTE: this is not currently used in production. when it is, it should be
    # converted into an EncryptedTextField.
    type: str
    type = models.TextField(choices=Type.choices)  # type: ignore[assignment]

    class Meta(TypedModelMeta):
        unique_together = ["user", "type"]

    def __str__(self):
        return str(self.type)
