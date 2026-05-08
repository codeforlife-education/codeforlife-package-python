"""
© Ocado Group
Created on 29/01/2024 at 16:46:24(+00:00).
"""

import string
import typing as t

from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.db.utils import IntegrityError
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from ...models import EncryptedModel
from ...models.fields import EncryptedTextField
from ...types import Validators
from ...validators import CharSetValidatorBuilder

if t.TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext.db.models import TypedModelMeta

    from .user import User
else:
    TypedModelMeta = object


class OtpBypassToken(EncryptedModel):
    """A single use token to bypass a user's OTP authentication factor."""

    associated_data = "otp_bypass_token"
    length = 8
    allowed_chars = string.ascii_lowercase
    max_count = 10
    validators: Validators = [
        MinLengthValidator(length),
        MaxLengthValidator(length),
        CharSetValidatorBuilder(
            allowed_chars,
            "lowercase alpha characters (a-z)",
        ),
    ]

    # pylint: disable-next=missing-class-docstring,too-few-public-methods
    class Manager(EncryptedModel.Manager["OtpBypassToken"]):
        def bulk_create(self, user: "User"):  # type: ignore[override]
            """Bulk create OTP-bypass tokens.

            Args:
                otp_bypass_tokens: The token values to be hashed.

            Returns:
                Many OtpBypassToken instances.
            """
            tokens: t.Set[str] = set()
            while len(tokens) < OtpBypassToken.max_count:
                tokens.add(
                    get_random_string(
                        OtpBypassToken.length,
                        OtpBypassToken.allowed_chars,
                    )
                )

            user.otp_bypass_tokens.all().delete()

            otp_bypass_tokens = [
                OtpBypassToken(user=user, token=token) for token in tokens
            ]
            for otp_bypass_token in otp_bypass_tokens:
                otp_bypass_token.save()

            return otp_bypass_tokens

    objects: Manager = Manager()  # type: ignore[assignment]

    user: "User"
    user = models.ForeignKey(  # type: ignore[assignment]
        "user.User",
        related_name="otp_bypass_tokens",
        on_delete=models.CASCADE,
    )

    token: str
    token = EncryptedTextField(  # type: ignore[assignment]
        associated_data="token",
        verbose_name=_("token"),
        help_text=_("The encrypted equivalent of the token."),
    )

    class Meta(TypedModelMeta):
        verbose_name = _("OTP bypass token")
        verbose_name_plural = _("OTP bypass tokens")

    @property
    def dek_aead(self):
        return self.user.dek_aead  # type: ignore[attr-defined]

    def save(self, *args, **kwargs):
        raise IntegrityError("Cannot create or update a single instance.")

    def check_token(self, token: str):
        """Check if the token matches.

        Args:
            token: Token to check.

        Returns:
            A boolean designating if the token matches.
        """
        if self.token == token.lower():
            self.delete()
            return True

        return False
