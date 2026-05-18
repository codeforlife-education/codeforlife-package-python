"""
© Ocado Group
Created on 13/05/2026 at 12:17:05(+01:00).
"""

from functools import wraps

from ...types import PropertySetter, Validator


def validated_field_setter(*validators: Validator, blank=False, null=False):
    """Decorator to apply validators to a property setter method.

    Args:
        *validators: Validator functions to apply to the value.
        blank: If True, allows empty string values without validation.
        null: If True, allows None values without validation.
    """

    def decorator(fset: PropertySetter) -> PropertySetter:
        @wraps(fset)
        def wrapped(instance, value):
            if (value != "" or not blank) and (value is not None or not null):
                for validator in validators:
                    validator(value)  # should raise ValidationError if invalid

            return fset(instance, value)

        return wrapped

    return decorator
