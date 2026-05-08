"""
© Ocado Group
Created on 10/02/2026 at 14:00:56(+00:00).

Models that have been carried over from the old schema but are not yet fully
integrated into the new schema. These models are expected to be refactored and
integrated or removed in the new schema in the future.
"""

import typing as t
from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...models import EncryptedModel
from ...models.fields import EncryptedTextField, Sha256Field

if t.TYPE_CHECKING:  # pragma: no cover
    from datetime import datetime

    from django_stubs_ext.db.models import TypedModelMeta

    from .klass import Class
    from .school import School
    from .student import Student
    from .teacher import Teacher
    from .user import User
else:
    TypedModelMeta = object


class UserSession(models.Model):
    """A model to track user sessions."""

    user: "User"
    user = models.ForeignKey(  # type: ignore[assignment]
        "user.User",
        on_delete=models.CASCADE,
    )

    login_time: "datetime"
    login_time = models.DateTimeField(  # type: ignore[assignment]
        default=timezone.now
    )

    school: t.Optional["School"]
    school = models.ForeignKey(  # type: ignore[assignment]
        "user.School",
        null=True,
        on_delete=models.SET_NULL,
    )

    class_field: t.Optional["Class"]
    class_field = models.ForeignKey(  # type: ignore[assignment]
        "user.Class",
        null=True,
        on_delete=models.SET_NULL,
    )

    # for student login
    login_type: t.Optional[str]
    login_type = models.CharField(  # type: ignore[assignment]
        max_length=100,
        null=True,
    )

    def __str__(self):
        return f"{self.user} login: {self.login_time} type: {self.login_type}"


class JoinReleaseStudent(models.Model):
    """
    To keep track when a student is released to be independent student or
    joins a class to be a school student.
    """

    JOIN = "join"
    RELEASE = "release"

    student: "Student"
    student = models.ForeignKey(  # type: ignore[assignment]
        "user.Student",
        related_name="student",
        on_delete=models.CASCADE,
    )

    # either "release" or "join"
    action_type: str
    action_type = models.CharField(max_length=64)  # type: ignore[assignment]

    action_time: "datetime"
    action_time = models.DateTimeField(  # type: ignore[assignment]
        default=timezone.now
    )


class TotalActivity(models.Model):
    """
    A model to record total activity. Meant to only have one entry which
    records all total activity. An example of this is total ever registrations.
    """

    teacher_registrations: int
    teacher_registrations = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    student_registrations: int
    student_registrations = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    independent_registrations: int
    independent_registrations = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    anonymised_unverified_teachers: int
    anonymised_unverified_teachers = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    anonymised_unverified_independents: int
    anonymised_unverified_independents = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    class Meta(TypedModelMeta):
        verbose_name_plural = "Total activity"

    def __str__(self):
        return "Total activity"


class DailyActivity(models.Model):
    """
    A model to record sets of daily activity. Currently used to record the
    amount of student details download clicks, through the CSV and login
    cards methods, per day.
    """

    date: "datetime"
    date = models.DateField(default=timezone.now)  # type: ignore[assignment]

    csv_click_count: int
    csv_click_count = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    login_cards_click_count: int
    login_cards_click_count = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    primary_coding_club_downloads: int
    primary_coding_club_downloads = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    python_coding_club_downloads: int
    python_coding_club_downloads = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    level_control_submits: int
    level_control_submits = models.PositiveBigIntegerField(
        default=0
    )  # type: ignore[assignment]

    teacher_lockout_resets: int
    teacher_lockout_resets = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    indy_lockout_resets: int
    indy_lockout_resets = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    school_student_lockout_resets: int
    school_student_lockout_resets = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    anonymised_unverified_teachers: int
    anonymised_unverified_teachers = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    anonymised_unverified_independents: int
    anonymised_unverified_independents = models.PositiveIntegerField(
        default=0
    )  # type: ignore[assignment]

    class Meta(TypedModelMeta):
        verbose_name_plural = "Daily activities"

    def __str__(self):
        # pylint: disable-next=line-too-long
        return f"Activity on {self.date}: CSV clicks: {self.csv_click_count}, login cards clicks: {self.login_cards_click_count}, primary pack downloads: {self.primary_coding_club_downloads}, python pack downloads: {self.python_coding_club_downloads}, level control submits: {self.level_control_submits}, teacher lockout resets: {self.teacher_lockout_resets}, indy lockout resets: {self.indy_lockout_resets}, school student lockout resets: {self.school_student_lockout_resets}, unverified teachers anonymised: {self.anonymised_unverified_teachers}, unverified independents anonymised: {self.anonymised_unverified_independents}"


class SchoolTeacherInvitationModelManager(
    EncryptedModel.Manager["SchoolTeacherInvitation"]
):
    """
    A custom model manager for the SchoolTeacherInvitation model to filter out
    inactive invitations by default.
    """

    def get_original_queryset(self):
        """
        Get the original queryset without filtering out inactive invitations.
        """
        return super().get_queryset()

    def get_queryset(self):
        """
        Get the queryset for the SchoolTeacherInvitation model, filtering out
        inactive invitations by default.
        """
        return super().get_queryset().filter(is_active=True)


# pylint: disable-next=too-many-instance-attributes
class SchoolTeacherInvitation(EncryptedModel):
    """
    A model to track invitations for teachers to join a school. This is meant to
    be used when a teacher invites another teacher to join their school, and the
    invitation needs to be tracked until the invited teacher accepts or declines
    the invitation, or the invitation expires.
    """

    associated_data = "school_teacher_invitation"
    field_aliases = {
        "token": {"_token_plain", "_token_enc", "_token_hash"},
        "invited_teacher_first_name": {
            "_invited_teacher_first_name_plain",
            "_invited_teacher_first_name_enc",
        },
        "invited_teacher_last_name": {
            "_invited_teacher_last_name_plain",
            "_invited_teacher_last_name_enc",
        },
        "invited_teacher_email": {
            "_invited_teacher_email_plain",
            "_invited_teacher_email_enc",
        },
    }

    # --------------------------------------------------------------------------
    # Token
    # --------------------------------------------------------------------------

    _token_hash = Sha256Field(
        verbose_name=_("token hash"),
        null=True,
        db_column="token_hash",
    )
    _token_plain: str
    _token_plain = models.CharField(max_length=88)  # type: ignore[assignment]
    _token_enc = EncryptedTextField(
        associated_data="token",
        null=True,
        verbose_name=_("token"),
        db_column="token_enc",
    )

    @property
    def token(self):
        """Get the decrypted token value."""
        if self._token_enc is not None:
            return EncryptedTextField.get(self, "_token_enc")
        return self._token_plain

    @token.setter
    def token(self, value: str):
        """Sets the token value."""
        self._token_plain = value
        EncryptedTextField.set(self, value, "_token_enc")
        Sha256Field.set(self, value, "_token_hash")

    # --------------------------------------------------------------------------

    school: t.Optional["School"]
    school = models.ForeignKey(  # type: ignore[assignment]
        "user.School",
        related_name="teacher_invitations",
        null=True,
        on_delete=models.SET_NULL,
    )

    from_teacher: t.Optional["Teacher"]
    from_teacher = models.ForeignKey(  # type: ignore[assignment]
        "user.Teacher",
        related_name="school_invitations",
        null=True,
        on_delete=models.SET_NULL,
    )

    # --------------------------------------------------------------------------
    # First name
    # --------------------------------------------------------------------------

    _invited_teacher_first_name_plain: str
    # pylint: disable-next=line-too-long
    _invited_teacher_first_name_plain = models.CharField(  # type: ignore[assignment]
        max_length=150
    )  # Same as User model
    _invited_teacher_first_name_enc = EncryptedTextField(
        associated_data="invited_teacher_first_name",
        null=True,
        verbose_name=_("invited teacher first name"),
        db_column="invited_teacher_first_name_enc",
    )

    @property
    def invited_teacher_first_name(self):
        """Get the decrypted invited teacher first name value."""
        if self._invited_teacher_first_name_enc is not None:
            return EncryptedTextField.get(
                self, "_invited_teacher_first_name_enc"
            )
        return self._invited_teacher_first_name_plain

    @invited_teacher_first_name.setter
    def invited_teacher_first_name(self, value: str):
        """Sets the invited teacher first name value."""
        self._invited_teacher_first_name_plain = value
        EncryptedTextField.set(self, value, "_invited_teacher_first_name_enc")

    # --------------------------------------------------------------------------
    # Last name
    # --------------------------------------------------------------------------

    _invited_teacher_last_name_plain: str
    # pylint: disable-next=line-too-long
    _invited_teacher_last_name_plain = models.CharField(  # type: ignore[assignment]
        max_length=150
    )  # Same as User model
    _invited_teacher_last_name_enc = EncryptedTextField(
        associated_data="invited_teacher_last_name",
        null=True,
        verbose_name=_("invited teacher last name"),
        db_column="invited_teacher_last_name_enc",
    )

    @property
    def invited_teacher_last_name(self):
        """Get the decrypted invited teacher last name value."""
        if self._invited_teacher_last_name_enc is not None:
            return EncryptedTextField.get(
                self, "_invited_teacher_last_name_enc"
            )
        return self._invited_teacher_last_name_plain

    @invited_teacher_last_name.setter
    def invited_teacher_last_name(self, value: str):
        """Sets the invited teacher last name value."""
        self._invited_teacher_last_name_plain = value
        EncryptedTextField.set(self, value, "_invited_teacher_last_name_enc")

    # --------------------------------------------------------------------------
    # Email
    # --------------------------------------------------------------------------

    # TODO: Switch to a CharField to be able to hold hashed value
    _invited_teacher_email_plain: str
    _invited_teacher_email_plain = (
        models.EmailField()  # type: ignore[assignment]
    )  # Same as User model
    _invited_teacher_email_enc = EncryptedTextField(
        associated_data="invited_teacher_email",
        null=True,
        verbose_name=_("invited teacher email"),
        db_column="invited_teacher_email_enc",
    )

    @property
    def invited_teacher_email(self):
        """Get the decrypted invited teacher email value."""
        if self._invited_teacher_email_enc is not None:
            return EncryptedTextField.get(self, "_invited_teacher_email_enc")
        return self._invited_teacher_email_plain

    @invited_teacher_email.setter
    def invited_teacher_email(self, value: str):
        """Sets the invited teacher email value."""
        self._invited_teacher_email_plain = value
        EncryptedTextField.set(self, value, "_invited_teacher_email_enc")

    # --------------------------------------------------------------------------

    invited_teacher_is_admin: bool
    invited_teacher_is_admin = models.BooleanField(  # type: ignore[assignment]
        default=False
    )

    expiry: "datetime"
    expiry = models.DateTimeField()  # type: ignore[assignment]

    # pylint: disable=duplicate-code
    creation_time: t.Optional["datetime"]
    creation_time = models.DateTimeField(  # type: ignore[assignment]
        default=timezone.now, null=True
    )

    is_active: bool
    is_active = models.BooleanField(default=True)  # type: ignore[assignment]
    # pylint: enable=duplicate-code

    objects: SchoolTeacherInvitationModelManager = (
        SchoolTeacherInvitationModelManager()  # type: ignore[assignment]
    )

    @property
    def is_expired(self):
        """Whether the invitation has expired based on the expiry datetime."""
        return self.expiry < timezone.now()

    def __str__(self):
        if self.school is None:
            return super().__str__()

        # pylint: disable-next=line-too-long
        return f"School teacher invitation for {self.invited_teacher_email} to {self.school.name}"

    def anonymise(self):
        """Anonymise the invitation."""
        self.invited_teacher_first_name = uuid4().hex
        self.invited_teacher_last_name = uuid4().hex
        self.invited_teacher_email = uuid4().hex
        self.is_active = False
        self.save()

    @property
    def dek_aead(self):
        if self.school:
            return self.school.dek_aead

        raise KeyError("Data Encryption Key (DEK) not found.")
