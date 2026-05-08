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

    from ..school import School
    from .user import User
else:
    TypedModelMeta = object

AnyUser = t.TypeVar("AnyUser", bound="User")


# pylint: disable-next=missing-class-docstring,too-few-public-methods
class SchoolTeacherUserManager(TeacherUserManager[AnyUser], t.Generic[AnyUser]):
    # pylint: disable-next=signature-differs,too-many-arguments,too-many-positional-arguments
    def create_user(  # type: ignore[override]
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        school: "School",
        is_admin: bool = False,
        is_verified: bool = False,
        **extra_fields,
    ):
        """Creates a user that is a teacher in a school."""
        return super().create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            school=school,
            is_admin=is_admin,
            is_verified=is_verified,
            **extra_fields,
        )

    def filter_users(self, queryset: QuerySet["User"]):
        """Filter users to include only school teachers."""
        return (
            super()
            .filter_users(queryset)
            .filter(new_teacher__school__isnull=False)
        )


# pylint: disable-next=too-many-ancestors
class SchoolTeacherUser(TeacherUser):
    """A user that is a teacher in a school."""

    class Meta(TypedModelMeta):
        proxy = True

    objects: SchoolTeacherUserManager[  # type: ignore[misc]
        "SchoolTeacherUser"
    ] = SchoolTeacherUserManager()  # type: ignore[assignment]

    @property
    def teacher(self):
        # pylint: disable-next=import-outside-toplevel,cyclic-import
        from ..teacher import SchoolTeacher, teacher_as_type

        teacher = super().teacher

        return teacher_as_type(teacher, SchoolTeacher) if teacher else None
