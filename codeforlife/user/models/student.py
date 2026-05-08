# TODO: remove this in new system
# mypy: disable-error-code="import-untyped"
"""
© Ocado Group
Created on 14/02/2024 at 17:16:44(+00:00).
"""

import typing as t
from uuid import uuid4

from django.db import models

if t.TYPE_CHECKING:  # pragma: no cover
    from datetime import datetime

    from django_stubs_ext.db.models import TypedModelMeta

    from .klass import Class
    from .user import User, UserProfile
else:
    TypedModelMeta = object


class StudentModelManager(models.Manager):
    """Manager for Student model."""

    def get_random_username(self):
        """Generate a random username that does not already exist."""
        # NOTE: avoid circular imports by importing here
        # pylint: disable-next=import-outside-toplevel
        from .user import User

        while True:
            random_username = uuid4().hex[:30]  # generate a random username
            if not User.objects.filter(
                _username_plain=random_username
            ).exists():
                return random_username

    # pylint: disable-next=invalid-name
    def schoolFactory(self, klass, name, password, login_id=None):
        """Factory method to create a student user associated with a class."""
        # NOTE: avoid circular imports by importing here
        # pylint: disable-next=import-outside-toplevel
        from .user import User, UserProfile

        user = User.objects.create_user(
            username=self.get_random_username(),
            password=password,
            first_name=name,
        )
        user_profile = UserProfile.objects.create(user=user)

        return Student.objects.create(
            class_field=klass,
            user=user_profile,
            new_user=user,
            login_id=login_id,
        )

    # pylint: disable-next=invalid-name
    def independentStudentFactory(self, name, email, password):
        """Factory method to create an independent student user."""
        # NOTE: avoid circular imports by importing here
        # pylint: disable-next=import-outside-toplevel
        from .user import User, UserProfile

        user = User.objects.create_user(
            username=email, email=email, password=password, first_name=name
        )

        user_profile = UserProfile.objects.create(user=user)

        return Student.objects.create(user=user_profile, new_user=user)


class Student(models.Model):
    """A student."""

    class_field: t.Optional["Class"]
    class_field = models.ForeignKey(  # type: ignore[assignment]
        "user.Class",
        related_name="students",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    # NOTE: hashed uuid used for the unique direct login url
    # TODO: this is currently hashed using sha256 without a salt. this should be
    # updated to use the Sha256Field which hashes the value using Django's
    # secret key as a salt. This will require generating new values for existing
    # students.
    login_id: str
    login_id = models.CharField(  # type: ignore[assignment]
        max_length=64,
        null=True,
    )

    # pylint: disable=duplicate-code
    user: "UserProfile"
    user = models.OneToOneField(  # type: ignore[assignment]
        "user.UserProfile",
        on_delete=models.CASCADE,
    )

    new_user: t.Optional["User"]
    new_user = models.OneToOneField(  # type: ignore[assignment]
        "user.User",
        related_name="new_student",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    # pylint: enable=duplicate-code

    pending_class_request: t.Optional["Class"]
    pending_class_request = models.ForeignKey(  # type: ignore[assignment]
        "user.Class",
        related_name="class_request",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    blocked_time: t.Optional["datetime"]
    blocked_time = models.DateTimeField(  # type: ignore[assignment]
        null=True,
        blank=True,
    )

    objects = StudentModelManager()

    def is_independent(self):
        """Whether the student is independent (not associated with a class)."""
        return not self.class_field

    def __str__(self):
        if self.new_user is None:
            return super().__str__()

        return f"{self.new_user.first_name} {self.new_user.last_name}"


# TODO: This model is legacy and should be removed in the new data schema.
class Independent(Student):
    """An independent student."""

    class_field: None  # type: ignore[assignment]

    class Meta(TypedModelMeta):
        proxy = True

    # pylint: disable-next=missing-class-docstring
    class Manager(StudentModelManager):
        # pylint: disable-next=missing-function-docstring
        def get_queryset(self):
            return super().get_queryset().filter(class_field__isnull=True)

    # pylint: disable-next=line-too-long
    objects: models.Manager["Independent"] = Manager()  # type: ignore[assignment,misc]
