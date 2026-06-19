"""
© Ocado Group
Created on 27/05/2026 at 15:38:57(+01:00).
"""

from ...types import Validator


def validate_value(value, *validators: Validator, blank=False, null=False):
    """Validate a field value using the provided validators.

    Validators should raise a ValidationError if the value is invalid.

    Args:
        value: The value to validate.
        *validators: Validator functions to apply to the value.
        blank: If True, allows empty string values without validation.
        null: If True, allows None values without validation.
    """

    if (value == "" and blank) or (value is None and null):
        return

    for validator in validators:
        validator(value)  # should raise ValidationError if invalid
