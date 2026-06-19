"""
© Ocado Group
Created on 14/08/2025 at 14:24:39(+01:00).

The user model and all of its proxies. Proxies help is to predefine filters and
user specific utilities.
"""

import typing as t

from .admin_school_teacher import (
    AdminSchoolTeacherUser,
    AdminSchoolTeacherUserManager,
)
from .contactable import ContactableUser, ContactableUserManager
from .google import GoogleUser, GoogleUserManager
from .independent import IndependentUser, IndependentUserManager
from .non_admin_school_teacher import (
    NonAdminSchoolTeacherUser,
    NonAdminSchoolTeacherUserManager,
)
from .non_school_teacher import (
    NonSchoolTeacherUser,
    NonSchoolTeacherUserManager,
)
from .school_teacher import SchoolTeacherUser, SchoolTeacherUserManager
from .student import StudentUser, StudentUserManager
from .teacher import TeacherUser, TeacherUserManager
from .user import AnyUser, User, UserManager, UserProfile

# pylint: disable-next=invalid-name
TypedUser = t.Union[
    TeacherUser,
    SchoolTeacherUser,
    AdminSchoolTeacherUser,
    NonAdminSchoolTeacherUser,
    NonSchoolTeacherUser,
    StudentUser,
    IndependentUser,
    GoogleUser,
]

AnyTypedUser = t.TypeVar("AnyTypedUser", bound=TypedUser)
