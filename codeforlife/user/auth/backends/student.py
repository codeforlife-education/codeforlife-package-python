"""
© Ocado Group
Created on 01/02/2024 at 14:48:17(+00:00).
"""

import typing as t

from ....request import HttpRequest
from ...models import StudentUser
from .base import BaseBackend


class StudentBackend(BaseBackend):
    """Authenticate a student using their first name, password and class ID."""

    user_class = StudentUser

    def authenticate(  # type: ignore[override]
        self,
        request: t.Optional[HttpRequest],
        first_name: t.Optional[str] = None,
        password: t.Optional[str] = None,
        class_id: t.Optional[str] = None,
        **kwargs
    ):
        if first_name is None or password is None or class_id is None:
            return None

        # pylint: disable=duplicate-code
        try:
            user = self.user_class.objects.get(
                _first_name_hash__sha256=first_name,
                new_student__class_field___access_code_hash__sha256=class_id,
            )
        except self.user_class.DoesNotExist:
            return None
        # pylint: enable=duplicate-code

        if user.check_password(password):
            return user

        return None
