"""
© Ocado Group
Created on 16/03/2026 at 15:01:24(+00:00).
"""

from ...tests import TestCase
from ...user.models import User
from .sha256 import Sha256Field


# pylint: disable-next=missing-class-docstring
class Sha256FieldTests(TestCase):
    fixtures = ["school_1"]

    def test_init__editable_not_allowed(self):
        """Cannot create Sha256Field with editable=True."""
        with self.assert_raises_validation_error(code="editable_not_allowed"):
            Sha256Field(editable=True)  # type: ignore[arg-type]

    def test_init__max_length_not_64(self):
        """Cannot create Sha256Field with max_length not equal to 64."""
        with self.assert_raises_validation_error(code="max_length_not_64"):
            Sha256Field(max_length=32)  # type: ignore[arg-type]

    def test_set__none(self):
        """Setting field to None sets to None."""
        user = User(_email_hash=None)
        assert user.__dict__["_email_hash"] is None

    def test_hash(self):
        """Hashing the same value produces the same hash of 64 characters."""
        value = "consistent_value"
        hashed_value = Sha256Field.hash(value)
        assert hashed_value == Sha256Field.hash(value)
        assert hashed_value != Sha256Field.hash("different_value")
        assert len(hashed_value) == 64

    def test_lookup__sha256(self):
        """
        `sha256` lookup hashes the right-hand side value before doing an exact
        match.
        """
        user = User.objects.filter(_email_hash__isnull=False).first()
        assert user
        # pylint: disable-next=protected-access
        assert user.email != user._email_hash
        assert User.objects.get(_email_hash__sha256=user.email) == user

    def test_lookup__sha256_in(self):
        """
        `sha256_in` lookup hashes each value in the list before doing an exact
        match.
        """
        user = User.objects.filter(_email_hash__isnull=False).first()
        assert user
        # pylint: disable-next=protected-access
        assert user.email != user._email_hash
        assert User.objects.get(_email_hash__sha256_in=[user.email]) == user
