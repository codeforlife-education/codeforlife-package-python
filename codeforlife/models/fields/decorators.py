"""
© Ocado Group
Created on 13/05/2026 at 12:17:05(+01:00).
"""

from functools import wraps

from ...types import PropertySetter, Validator


def validated_field_setter(*validators: Validator):
    """Decorator to apply validators to a property setter method."""

    def decorator(fset: PropertySetter) -> PropertySetter:
        @wraps(fset)
        def wrapped(instance, value):
            for validator in validators:
                validator(value)  # should raise ValidationError if invalid

            return fset(instance, value)

        return wrapped

    return decorator
