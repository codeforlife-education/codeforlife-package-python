# TODO: remove this in new system
# mypy: disable-error-code="import-untyped"
"""
© Ocado Group
Created on 05/02/2024 at 09:50:04(+00:00).
"""

import typing as t

from django.db.models.query import QuerySet

from .teacher import TeacherUser, TeacherUserManager

if t.TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext.db.models import TypedModelMeta

    from .user import User
else:
    TypedModelMeta = object

AnyUser = t.TypeVar("AnyUser", bound="User")


# pylint: disable-next=missing-class-docstring,too-few-public-methods
class NonSchoolTeacherUserManager(TeacherUserManager["NonSchoolTeacherUser"]):
    def filter_users(self, queryset: QuerySet["User"]):
        """Filter users to include only teachers not in a school."""
        return (
            super()
            .filter_users(queryset)
            .filter(new_teacher__school__isnull=True)
        )


# pylint: disable-next=too-many-ancestors
class NonSchoolTeacherUser(TeacherUser):
    """A user that is a teacher not in a school."""

    class Meta(TypedModelMeta):
        proxy = True

    objects: NonSchoolTeacherUserManager = (  # type: ignore[misc]
        NonSchoolTeacherUserManager()  # type: ignore[assignment]
    )

    @property
    def teacher(self):
        # pylint: disable-next=import-outside-toplevel
        from ..teacher import NonSchoolTeacher, teacher_as_type

        teacher = super().teacher

        return teacher_as_type(teacher, NonSchoolTeacher) if teacher else None
