# TODO: remove this in new system
# mypy: disable-error-code="import-untyped"
"""
© Ocado Group
Created on 05/02/2024 at 09:50:04(+00:00).
"""

import typing as t

from django.db.models import F
from django.db.models.query import QuerySet

from .contactable import ContactableUser, ContactableUserManager

if t.TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext.db.models import TypedModelMeta

    from ..student import Independent
    from .user import User
else:
    TypedModelMeta = object

AnyUser = t.TypeVar("AnyUser", bound="User")


# pylint: disable-next=missing-class-docstring,too-few-public-methods
class IndependentUserManager(ContactableUserManager["IndependentUser"]):
    def filter_users(self, queryset: QuerySet["User"]):
        return (
            super()
            .filter_users(queryset)
            .filter(
                new_teacher__isnull=True,
                # TODO: student__isnull=True in new model
                new_student__isnull=False,
                new_student__class_field__isnull=True,
            )
        )

    def get_queryset(self):
        return super().get_queryset().prefetch_related("new_student")

    # pylint: disable-next=arguments-differ
    def create_user(  # type: ignore[override]
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        **extra_fields,
    ):
        """Create an independent-user."""
        # pylint: disable=import-outside-toplevel
        from ..other import TotalActivity
        from ..student import Student
        from .user import UserProfile

        # pylint: enable=import-outside-toplevel

        assert "username" not in extra_fields

        # pylint: disable=duplicate-code
        user = super().create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        # pylint: enable=duplicate-code

        # NOTE: Indy user needs a student object for now while we use the
        # old models.
        # TODO: Remove this once using the new models.
        Student.objects.create(
            new_user=user,
            user=UserProfile.objects.create(user=user),
        )

        # TODO: delete this in new data schema
        TotalActivity.objects.update(
            independent_registrations=F("independent_registrations") + 1
        )

        return user


# pylint: disable-next=too-many-ancestors
class IndependentUser(ContactableUser):
    """A user that is an independent learner."""

    teacher: None
    student: "Independent"  # TODO: set to None in new model

    class Meta(TypedModelMeta):
        proxy = True

    objects: IndependentUserManager = (  # type: ignore[misc]
        IndependentUserManager()  # type: ignore[assignment]
    )
