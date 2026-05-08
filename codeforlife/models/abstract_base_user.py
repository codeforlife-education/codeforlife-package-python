"""
© Ocado Group
Created on 06/11/2024 at 16:38:15(+00:00).
"""

import typing as t
from functools import cached_property

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser as _AbstractBaseUser
from django.utils.translation import gettext_lazy as _

from .base import Model

if t.TYPE_CHECKING:
    from django_stubs_ext.db.models import TypedModelMeta

    from .abstract_base_session import AbstractBaseSession
else:
    TypedModelMeta = object


class AbstractBaseUser(Model, _AbstractBaseUser):
    """
    Base user class to be inherited by all user classes.
    https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
    """

    pk: int
    session: "AbstractBaseSession"

    # pylint: disable-next=missing-class-docstring,too-few-public-methods
    class Meta(TypedModelMeta):
        abstract = True
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @cached_property
    def _session_class(self):
        return t.cast(
            t.Type["AbstractBaseSession"],
            apps.get_model(
                app_label=(
                    t.cast(str, settings.SESSION_ENGINE)
                    .lower()
                    .removesuffix(".models.session")
                    .split(".")[-1]
                ),
                model_name="session",
            ),
        )

    @property
    def is_authenticated(self):
        """A flag designating if this contributor has authenticated."""
        try:
            return self.is_active and not self.session.is_expired
        except self._session_class.DoesNotExist:
            return False
