# TODO: remove this in new system
# mypy: disable-error-code="import-untyped"
"""
© Ocado Group
Created on 05/02/2024 at 09:50:04(+00:00).
"""

import typing as t

from django.db.models.query import QuerySet

from .... import mail
from .user import User, UserManager

if t.TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext.db.models import TypedModelMeta
else:
    TypedModelMeta = object

AnyUser = t.TypeVar("AnyUser", bound=User)


# pylint: disable-next=missing-class-docstring,too-few-public-methods
class ContactableUserManager(UserManager[AnyUser], t.Generic[AnyUser]):
    def filter_users(self, queryset: QuerySet[User]):
        return queryset.exclude(_email_plain__isnull=True).exclude(
            _email_plain=""
        )


# pylint: disable-next=too-many-ancestors
class ContactableUser(User):
    """A user that can be contacted."""

    class Meta(TypedModelMeta):
        proxy = True

    objects: ContactableUserManager = (  # type: ignore[misc]
        ContactableUserManager()
    )

    def add_contact_to_dot_digital(self):
        """Add contact info to DotDigital."""
        mail.add_contact(self.email)

    def remove_contact_from_dot_digital(self):
        """Remove contact info from DotDigital."""
        mail.remove_contact(self.email)

    # pylint: disable-next=arguments-differ
    def email_user(  # type: ignore[override]
        self,
        campaign_id: int,
        personalization_values: t.Optional[t.Dict[str, str]] = None,
        **kwargs,
    ):
        """Send an email to this user using DotDigital."""
        kwargs["to_addresses"] = [self.email]
        mail.send_mail(
            campaign_id=campaign_id,
            personalization_values=personalization_values,
            **kwargs,
        )
