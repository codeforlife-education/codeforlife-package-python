"""
© Ocado Group
Created on 15/01/2024 at 15:32:54(+00:00).

Reusable type hints.
"""

import typing as t

CookieSamesite = t.Optional[t.Literal["Lax", "Strict", "None", False]]

Env = t.Literal["local", "development", "staging", "production"]

Args = t.Tuple[t.Any, ...]
KwArgs = t.Dict[str, t.Any]

JsonList = t.List["JsonValue"]
JsonDict = t.Dict[str, "JsonValue"]
JsonValue = t.Union[None, int, float, str, bool, JsonList, JsonDict]

DataDict = t.Dict[str, t.Any]
OrderedDataDict = t.OrderedDict[str, t.Any]

Validators = t.Sequence[t.Callable]

LogLevel = t.Literal[
    "CRITICAL",
    "FATAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG",
]


def get_arg(cls: t.Type[t.Any], index: int, orig_base: int = 0):
    """Get a type arg from a class.

    Args:
        cls: The class to get the type arg from.
        index: The index of the type arg to get.
        orig_base: The base class to get the type arg from.

    Returns:
        The type arg from the class.
    """
    return t.get_args(cls.__orig_bases__[orig_base])[index]


class OAuth2TokenFromRefreshDict(t.TypedDict):
    """An OAuth 2.0 token given in exchange for a refresh token."""

    access_token: str
    token_type: str
    scope: str
    expires_in: int
    error: t.NotRequired[dict]


class OAuth2TokenFromCodeDict(t.TypedDict):
    """An OAuth 2.0 token given in exchange for a code."""

    access_token: str
    token_type: str
    scope: str
    expires_in: int
    refresh_token: str
    error: t.NotRequired[dict]
