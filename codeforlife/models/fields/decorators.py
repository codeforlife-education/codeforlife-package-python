"""
© Ocado Group
Created on 13/05/2026 at 12:17:05(+01:00).
"""

from functools import wraps

from ...types import PropertySetter, Validator
from .utils import validate_value


def validated_field_setter(*validators: Validator, blank=False, null=False):
    """Decorator to apply validators to a property setter method.

    Validators should raise a ValidationError if the value is invalid.

    Args:
        *validators: Validator functions to apply to the value.
        blank: If True, allows empty string values without validation.
        null: If True, allows None values without validation.
    """

    def decorator(fset: PropertySetter) -> PropertySetter:
        @wraps(fset)
        def wrapped(instance, value):
            validate_value(value, *validators, blank=blank, null=null)
            return fset(instance, value)

        return wrapped

    return decorator
