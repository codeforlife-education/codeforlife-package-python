# TODO: remove this in new system
# mypy: disable-error-code="import-untyped"
"""
© Ocado Group
Created on 05/02/2024 at 09:50:04(+00:00).
"""

import typing as t

from django.db.models.query import QuerySet

from .school_teacher import SchoolTeacherUser, SchoolTeacherUserManager

if t.TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext.db.models import TypedModelMeta

    from .user import User
else:
    TypedModelMeta = object

AnyUser = t.TypeVar("AnyUser", bound="User")


# pylint: disable-next=missing-class-docstring,too-few-public-methods
class NonAdminSchoolTeacherUserManager(
    SchoolTeacherUserManager["NonAdminSchoolTeacherUser"]
):
    def filter_users(self, queryset: QuerySet["User"]):
        """Filter users to include only non-admin school teachers."""
        return (
            super().filter_users(queryset).filter(new_teacher__is_admin=False)
        )


# pylint: disable-next=too-many-ancestors
class NonAdminSchoolTeacherUser(SchoolTeacherUser):
    """A user that is a non-admin-teacher in a school."""

    class Meta(TypedModelMeta):
        proxy = True

    objects: NonAdminSchoolTeacherUserManager = (  # type: ignore[misc]
        NonAdminSchoolTeacherUserManager()  # type: ignore[assignment]
    )

    @property
    def teacher(self):
        # pylint: disable-next=import-outside-toplevel
        from ..teacher import NonAdminSchoolTeacher, teacher_as_type

        teacher = super().teacher

        return (
            teacher_as_type(teacher, NonAdminSchoolTeacher) if teacher else None
        )
