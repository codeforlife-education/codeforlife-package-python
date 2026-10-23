"""
© Ocado Group
Created on 21/03/2025 at 16:24:21(+00:00).

Base character set validators.
"""

import re
import typing as t

from ..enhanced_regex import EnhancedRegexValidator

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments


class CharSetValidator(EnhancedRegexValidator):
    """Validates all characters are within the allowed set."""

    def __init__(
        self,
        char_set: str,
        message: str,
        code: t.Optional[str] = None,
        inverse_match: t.Optional[bool] = None,
        flags: t.Optional[re.RegexFlag] = None,
    ):
        super().__init__(
            regex=f"^[{char_set}]*$",
            message=message,
            code=code,
            inverse_match=inverse_match,
            flags=flags,
        )


class CharSetValidatorBuilder(CharSetValidator):
    """Build a character set with optional addons for reusability."""

    def __init__(
        self,
        char_set: str,
        description: str,
        code: t.Optional[str] = None,
        inverse_match: t.Optional[bool] = None,
        flags: t.Optional[re.RegexFlag] = None,
        spaces: bool = False,
        special_chars: str = "",
    ):
        message = f"can only contain: {description}"

        if spaces:
            char_set += " "
            message += ", spaces"
        if special_chars:
            char_set += re.escape(special_chars)
            message += f", special characters ({special_chars})"

        super().__init__(
            char_set=char_set,
            message=message,
            code=code,
            inverse_match=inverse_match,
            flags=flags,
        )
