"""
© Ocado Group
Created on 16/03/2026 at 17:35:19(+00:00).

Deterministic one-way hashing helpers for queryable sensitive values.

`Sha256Field` stores an HMAC-SHA256 digest (hex string) derived from a
plaintext input and the Django `SECRET_KEY`. This makes equality matching
possible without storing plaintext values.

Custom lookups are registered to keep querying ergonomic:

- `__sha256`: hashes a single right-hand side plaintext value.
- `__sha256_in`: hashes each plaintext value in an iterable.

This pattern is typically paired with encrypted fields when data must remain
encrypted at rest but still needs deterministic lookup support.
"""

import hmac
import typing as t
from hashlib import sha256

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import CharField, Model, lookups


class Sha256Field(CharField):
    """A CharField for deterministic, one-way hashed values."""

    def __init__(
        self,
        editable: t.Literal[False] = False,
        max_length: t.Literal[64] = 64,  # Length of SHA-256 hash in hexadecimal
        **kwargs,
    ):
        if editable:
            raise ValidationError(
                f"{self.__class__.__name__} cannot be editable.",
                code="editable_not_allowed",
            )
        if max_length != 64:
            raise ValidationError(
                f"{self.__class__.__name__} must have max_length of 64 to "
                "store a SHA-256 hash in hexadecimal.",
                code="max_length_not_64",
            )

        super().__init__(editable=editable, max_length=max_length, **kwargs)

    @staticmethod
    def hash(value: str):
        """Create a consistent, salted hash of a value.

        Args:
            value: The value to hash.

        Returns:
            A hash of the value salted with the Django secret key.
        """
        return hmac.new(
            key=settings.SECRET_KEY.encode("utf-8"),
            msg=value.encode("utf-8"),
            digestmod=sha256,
        ).hexdigest()

    @classmethod
    def set(cls, instance: Model, value: t.Optional[str], field_name: str):
        """
        Hash and assign a plaintext value to a Sha256Field.

        Args:
            instance: The model instance on which to set the value.
            value: The plaintext value to hash and set.
            field_name: The name of the Sha256Field on the model.
        """
        if value is not None:
            value = cls.hash(value)

        setattr(instance, field_name, value)


# pylint: disable-next=abstract-method
class Sha256ExactLookup(lookups.Exact):
    """
    A lookup that hashes a plaintext right-hand side value before comparing.

    This allows querying a hashed field with a plain text value, e.g.:
    `User.objects.filter(_email_hash__sha256="user@example.com")`
    """

    rhs: t.Optional[str]

    lookup_name = "sha256"

    def process_rhs(self, compiler, connection):
        sql, params = super().process_rhs(compiler, connection)

        return sql, params if self.rhs is None else [Sha256Field.hash(self.rhs)]

    def get_rhs_op(self, connection, rhs):
        """
        Get the operator for the right-hand side of the expression.

        We force it to use the '=' operator from the 'exact' lookup.
        """
        return connection.operators["exact"] % rhs


# pylint: disable-next=abstract-method,too-many-ancestors
class Sha256InLookup(lookups.In):
    """
    A lookup that hashes plaintext right-hand side values before comparing.

    This allows querying a hashed field with plain text values, e.g.:
    `User.objects.filter(_email_hash__sha256_in=["user@example.com"])`
    """

    rhs: t.Optional[t.Iterable[str]]

    lookup_name = f"{Sha256ExactLookup.lookup_name}_in"

    def process_rhs(self, compiler, connection):
        sql, params = super().process_rhs(compiler, connection)

        return sql, (
            params
            if self.rhs is None
            else [Sha256Field.hash(value) for value in self.rhs]
        )


Sha256Field.register_lookup(Sha256ExactLookup)
Sha256Field.register_lookup(Sha256InLookup)
