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
class AdminSchoolTeacherUserManager(
    SchoolTeacherUserManager["AdminSchoolTeacherUser"]
):
    def filter_users(self, queryset: QuerySet["User"]):
        """Filter users to include only admin school teachers."""
        return super().filter_users(queryset).filter(new_teacher__is_admin=True)


# pylint: disable-next=too-many-ancestors
class AdminSchoolTeacherUser(SchoolTeacherUser):
    """A user that is an admin-teacher in a school."""

    class Meta(TypedModelMeta):
        proxy = True

    objects: AdminSchoolTeacherUserManager = (  # type: ignore[misc]
        AdminSchoolTeacherUserManager()  # type: ignore[assignment]
    )

    @property
    def teacher(self):
        # pylint: disable-next=import-outside-toplevel
        from ..teacher import AdminSchoolTeacher, teacher_as_type

        teacher = super().teacher

        return teacher_as_type(teacher, AdminSchoolTeacher) if teacher else None
