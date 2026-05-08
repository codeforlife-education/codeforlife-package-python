# TODO: remove this in new system
# mypy: disable-error-code="import-untyped"
"""
© Ocado Group
Created on 05/02/2024 at 09:50:04(+00:00).
"""

import typing as t
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import UserManager as _UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pyotp import TOTP

from ....models import AbstractBaseUser, DataEncryptionKeyModel
from ....models.fields import EncryptedTextField, Sha256Field
from ....types import Validators
from ....validators import UnicodeAlphanumericCharSetValidator

if t.TYPE_CHECKING:  # pragma: no cover
    from ..auth_factor import AuthFactor
    from ..otp_bypass_token import OtpBypassToken
    from ..session import Session
    from ..student import Student
    from ..teacher import Teacher


# TODO: add to model validators in new schema.
user_first_name_validators: Validators = [
    UnicodeAlphanumericCharSetValidator(
        spaces=True,
        special_chars="-'",
    )
]
user_last_name_validators: Validators = [
    UnicodeAlphanumericCharSetValidator(
        spaces=True,
        special_chars="-'",
    )
]


AnyUser = t.TypeVar("AnyUser", bound="User")


class UserManager(
    _UserManager[AnyUser],
    DataEncryptionKeyModel.Manager[AnyUser],
    t.Generic[AnyUser],
):
    """
    Manager for the User model that inherits Django's default manager and
    encrypted manager to handle encrypted fields.
    """

    def _create_user_object(
        self,
        username: str,
        email: t.Optional[str],
        password: t.Optional[str],
        **extra_fields,
    ):
        self._inject_dek_kwarg(extra_fields)
        return super()._create_user_object(  # type: ignore[misc]
            username=username, email=email, password=password, **extra_fields
        )

    # pylint: disable=missing-function-docstring

    # @classmethod
    # def normalize_email(cls, email):
    #     return super().normalize_email(email).lower()

    # def get_by_natural_key(self, username):
    #     return self.get(_username_hash__sha256=username)

    # async def aget_by_natural_key(self, username):
    #     return await self.aget(_username_hash__sha256=username)

    # pylint: enable=missing-function-docstring

    def filter_users(self, queryset: QuerySet["User"]):
        """Filter the users to the specific type.

        Args:
            queryset: The queryset of users to filter.

        Returns:
            A subset of the queryset of users.
        """
        return queryset

    # pylint: disable-next=missing-function-docstring
    def get_queryset(self):
        queryset = super().get_queryset()
        return (
            queryset
            if getattr(settings, "OLD_SYSTEM", True)
            else self.filter_users(queryset.filter(is_active=True))
        )


# pylint: disable-next=too-many-ancestors,too-many-instance-attributes
class User(AbstractBaseUser, PermissionsMixin, DataEncryptionKeyModel):
    """A Code for Life user."""

    associated_data = "user"
    field_aliases = {
        "username": {"_username_plain", "_username_enc", "_username_hash"},
        "first_name": {
            "_first_name_plain",
            "_first_name_enc",
            "_first_name_hash",
        },
        "last_name": {"_last_name_plain", "_last_name_enc"},
        "email": {"_email_plain", "_email_enc", "_email_hash"},
    }

    EMAIL_FIELD = "_email_plain"
    USERNAME_FIELD = "_username_plain"
    REQUIRED_FIELDS = ["_email_plain"]
    credential_fields = frozenset(["email", "password"])

    _password: t.Optional[str]

    id: int  # type: ignore[assignment]
    auth_factors: QuerySet["AuthFactor"]  # type: ignore[assignment,misc]
    # pylint: disable-next=line-too-long
    otp_bypass_tokens: QuerySet["OtpBypassToken"]  # type: ignore[assignment,misc]
    session: "Session"  # type: ignore[assignment]
    userprofile: "UserProfile"

    # --------------------------------------------------------------------------
    # Username
    # --------------------------------------------------------------------------

    _username_hash = Sha256Field(
        verbose_name=_("username hash"),
        db_column="username_hash",
        unique=True,
        null=True,
    )
    _username_plain = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. "
            "Letters, digits and @/./+/-/_ only."
        ),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    _username_enc = EncryptedTextField(
        associated_data="username",
        db_column="username_enc",
        null=True,
        verbose_name=_("username"),
    )

    @property
    def username(self):
        """The user's username."""
        if self._username_enc is not None:
            return EncryptedTextField.get(self, "_username_enc")
        return self._username_plain

    @username.setter
    def username(self, value: str):
        """Set the user's username."""
        self._username_plain = value
        EncryptedTextField.set(self, value, "_username_enc")
        Sha256Field.set(self, value, "_username_hash")

    # --------------------------------------------------------------------------
    # First name
    # --------------------------------------------------------------------------

    _first_name_hash = Sha256Field(
        verbose_name=_("first name hash"),
        db_column="first_name_hash",
        null=True,
    )
    _first_name_plain = models.CharField(
        _("first name"), max_length=150, blank=True
    )
    _first_name_enc = EncryptedTextField(
        associated_data="first_name",
        db_column="first_name_enc",
        null=True,
        verbose_name=_("first name"),
    )

    @property
    def first_name(self):
        """The user's first name."""
        if self._first_name_enc is not None:
            return EncryptedTextField.get(self, "_first_name_enc")
        return self._first_name_plain

    @first_name.setter
    def first_name(self, value: str):
        """Set the user's first name."""
        self._first_name_plain = value
        EncryptedTextField.set(self, value, "_first_name_enc")
        Sha256Field.set(self, value, "_first_name_hash")

    # --------------------------------------------------------------------------
    # Last name
    # --------------------------------------------------------------------------

    _last_name_plain = models.CharField(
        _("last name"), max_length=150, blank=True
    )
    _last_name_enc = EncryptedTextField(
        associated_data="last_name",
        db_column="last_name_enc",
        null=True,
        verbose_name=_("last name"),
    )

    @property
    def last_name(self):
        """The user's last name."""
        if self._last_name_enc is not None:
            return EncryptedTextField.get(self, "_last_name_enc")
        return self._last_name_plain

    @last_name.setter
    def last_name(self, value: str):
        """Set the user's last name."""
        self._last_name_plain = value
        EncryptedTextField.set(self, value, "_last_name_enc")

    # --------------------------------------------------------------------------
    # Email
    # --------------------------------------------------------------------------

    _email_hash = Sha256Field(
        verbose_name=_("email hash"),
        db_column="email_hash",
        null=True,
    )
    _email_plain = models.EmailField(_("email address"), blank=True)
    _email_enc = EncryptedTextField(
        associated_data="email",
        db_column="email_enc",
        null=True,
        verbose_name=_("email address"),
    )

    @property
    def email(self):
        """The user's email address."""
        if self._email_enc is not None:
            return EncryptedTextField.get(self, "_email_enc")
        return self._email_plain

    @email.setter
    def email(self, value: str):
        """Set the user's email address."""
        value = self.__class__.objects.normalize_email(value)
        self._email_plain = value
        EncryptedTextField.set(self, value, "_email_enc")
        Sha256Field.set(self, value, "_email_hash")

    # --------------------------------------------------------------------------
    # Other
    # --------------------------------------------------------------------------

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."
        ),
    )

    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    # TODO: remove in new schema
    password: str  # type: ignore[assignment]
    password = models.CharField(  # type: ignore[assignment]
        _("password"),
        max_length=128,
    )

    # TODO: remove in new schema
    last_login: t.Optional[datetime]  # type: ignore[assignment]
    last_login = models.DateTimeField(  # type: ignore[assignment]
        _("last login"),
        blank=True,
        null=True,
    )

    objects: UserManager[  # type: ignore[misc]
        "User"
    ] = UserManager()  # type: ignore[assignment]

    @property
    def is_authenticated(self):
        return (
            True
            if getattr(settings, "OLD_SYSTEM", True)
            else (
                not self.session.auth_factors.exists()
                and self.userprofile.is_verified
                if super().is_authenticated
                else False
            )
        )

    @property
    def student(self) -> t.Optional["Student"]:
        """A user's student-profile."""
        # pylint: disable-next=import-outside-toplevel
        from ..student import Student

        try:
            # pylint: disable-next=no-member
            return self.new_student  # type: ignore[attr-defined]
        except Student.DoesNotExist:
            return None

    @property
    def teacher(self) -> t.Optional["Teacher"]:
        """A user's teacher-profile."""
        # pylint: disable-next=import-outside-toplevel
        from ..teacher import Teacher

        try:
            # pylint: disable-next=no-member
            return self.new_teacher  # type: ignore[attr-defined]
        except Teacher.DoesNotExist:
            return None

    @property
    def otp_secret(self):
        """Shorthand for user-profile field."""
        return self.userprofile.otp_secret

    @property
    def last_otp_for_time(self):
        """Shorthand for user-profile field."""
        return self.userprofile.last_otp_for_time

    # This property is set up differently in the old and new systems, so is not
    # defined on the model in the old system.
    is_verified: bool
    # @property
    # def is_verified(self):
    #     """Shorthand for user-profile field."""
    #     return self.userprofile.is_verified

    @property
    def totp(self):
        """Time-based one-time-password for user."""
        return TOTP(self.otp_secret)

    @property
    def totp_provisioning_uri(self):
        """URI provision for the user's time-based one-time-password."""
        return self.totp.provisioning_uri(
            name=self.email,
            issuer_name="Code for Life",
        )

    def as_type(self, user_class: t.Type["AnyUser"]):
        """Convert this generic user to a typed user.

        Args:
            user_class: The type of user to convert to.

        Returns:
            An instance of the typed user.
        """
        return user_class(
            pk=self.pk,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            is_active=self.is_active,
            email=self.email,
            is_staff=self.is_staff,
            date_joined=self.date_joined,
            is_superuser=self.is_superuser,
            password=self.password,
            last_login=self.last_login,
        )

    def anonymize(self):
        """Anonymize the user."""
        self.dek = None
        self.is_active = False
        self.save(update_fields=["dek", "is_active"])

        # self.userprofile.google_refresh_token = None
        # self.userprofile.google_sub = None
        # self.userprofile.save(
        #     update_fields=[
        #         "google_refresh_token",
        #         "google_sub",
        #     ]
        # )

    def __repr__(self):
        return f"<User: {self.pk}>"


if not getattr(settings, "OLD_SYSTEM", True):

    def is_verified(self: User):
        """Shorthand for user-profile field."""
        return self.userprofile.is_verified

    User.is_verified = property(fget=is_verified)  # type: ignore[assignment]


# TODO: merge the UserProfile model into the User model and delete it.
class UserProfile(models.Model):
    """A user's profile."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # NOTE: this is not currently used in production. when it is, it should be:
    # 1. moved to the User model
    # 2. made non-nullable with a default generator of a random string
    # 3. converted into an EncryptedTextField
    otp_secret = models.CharField(max_length=40, null=True, blank=True)

    last_otp_for_time = models.DateTimeField(null=True, blank=True)
    developer = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Google.
    google_refresh_token: t.Optional[str]
    # google_refresh_token = EncryptedCharField(
    #     # pylint: disable-next=protected-access
    #     max_length=1000 + len(EncryptedCharField._prefix),
    #     null=True,
    #     blank=True,
    # )
    google_sub: t.Optional[str]
    # google_sub = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def joined_recently(self):
        """Whether the user joined within the last week."""
        now = timezone.now()
        return now - timedelta(days=7) <= self.user.date_joined
