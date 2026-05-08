"""
© Ocado Group
Created on 09/04/2026 at 10:28:21(+00:00).
"""

import os
import typing as t
from functools import lru_cache
from threading import Event, RLock

import google_crc32c
from cachetools import Cache
from google.api_core.exceptions import NotFound
from google.cloud.secretmanager import SecretManagerServiceClient
from typing_extensions import TypeVar

if t.TYPE_CHECKING:
    from ..types import Env

T = TypeVar("T", default=None)
# pylint: disable-next=invalid-name
T2 = TypeVar("T2", default=None)

_LATEST_CACHE: Cache[str, t.Tuple[str, str]] = Cache(maxsize=256)
_LATEST_CACHE_LOCK = RLock()
_LATEST_CACHE_EVENTS: t.Dict[str, Event] = {}


@lru_cache(maxsize=1)  # This is a singleton, so we only want to create it once.
def _client():
    return SecretManagerServiceClient(
        client_options={
            "api_endpoint": (
                "secretmanager."
                + os.environ["GCP_SECRET_MANAGER_LOCATION"]
                + ".rep.googleapis.com"
            )
        }
    )


def _get_full_secret_name(name: str, version: str):
    return (
        f"projects/{os.environ['GOOGLE_CLOUD_PROJECT_ID']}"
        f"/locations/{os.environ['GCP_SECRET_MANAGER_LOCATION']}"
        f"/secrets/{name}"
        f"/versions/{version}"
    )


def _get_secret_metadata(name: str, version: str):
    try:
        return _client().get_secret_version(
            request={"name": _get_full_secret_name(name, version)}
        )
    except NotFound:
        return None


def _get_secret(name: str, version: str):
    try:
        response = _client().access_secret_version(
            request={"name": _get_full_secret_name(name, version)}
        )
    except NotFound:
        return None

    # Verify payload checksum.
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        raise ValueError(f"Invalid checksum for secret {name}.")

    return response.payload.data.decode("utf-8")


def _get_secret_with_latest_version_cache(name: str):
    version = "latest"

    # Single-flight: only one thread per secret does remote calls to prevent a
    # 'thundering herd' of remote calls when a secret is first accessed.
    with _LATEST_CACHE_LOCK:
        event = _LATEST_CACHE_EVENTS.get(name)
        if event is None:
            event = Event()
            _LATEST_CACHE_EVENTS[name] = event
            leader = True
        else:
            leader = False

    # Wait for leader to finish, then read cache result.
    if not leader:
        event.wait()
        with _LATEST_CACHE_LOCK:
            cached = _LATEST_CACHE.get(name)
            return None if cached is None else cached[1]

    try:
        meta = _get_secret_metadata(name, version)
        if meta is None:
            with _LATEST_CACHE_LOCK:
                _LATEST_CACHE.pop(name, None)
            return None

        with _LATEST_CACHE_LOCK:
            cached = _LATEST_CACHE.get(name)
            if cached is not None:
                etag, secret = cached
                if meta.etag == etag:
                    return secret

        secret = _get_secret(name, version)

        with _LATEST_CACHE_LOCK:
            if secret is None:
                _LATEST_CACHE.pop(name, None)
            else:
                _LATEST_CACHE[name] = (meta.etag, secret)

        return secret
    finally:
        with _LATEST_CACHE_LOCK:
            done = _LATEST_CACHE_EVENTS.pop(name, None)
            if done is not None:
                done.set()


@lru_cache(maxsize=200)  # Increase as needed, but be mindful of memory usage.
def _get_secret_with_specific_version_cache(name: str, version: str):
    return _get_secret(name, version)


@t.overload
def get_secret(
    name: str, default: None = None, version="latest", cache=True
) -> t.Union[str, None]: ...


@t.overload
def get_secret(
    name: str, default: T, version="latest", cache=True
) -> t.Union[str, T]: ...


def get_secret(
    name: str, default: t.Optional[T] = None, version="latest", cache=True
):
    """Get a secret from GCP Secret Manager.

    https://docs.cloud.google.com/secret-manager/docs/samples/secretmanager-access-regional-secret-version#secretmanager_access_regional_secret_version-python

    If running locally, this value will be read from environment variables.

    Args:
        name: The name of the secret.
        default: The default value to return if the secret does not exist.
        version: The version of the secret to access.
        cache: Whether to get & set the secret from/in the cache.

    Raises:
        ValueError: If the secret exists but has an invalid checksum.

    Returns:
        The value of the secret, or the default value if the secret does not
        exist.
    """
    env = t.cast("Env", os.getenv("ENV", "local"))
    if env == "local":
        return os.getenv(name, default)

    name = f"{env}_{name}".upper()
    value = (
        (
            _get_secret_with_latest_version_cache(name)
            if version == "latest"
            else _get_secret_with_specific_version_cache(name, version)
        )
        if cache
        else _get_secret(name, version)
    )

    return default if value is None else value


# pylint: disable-next=too-few-public-methods
class LatestSecret(t.Generic[T]):
    """
    A callable wrapper around `get_secret()` that allows you to define a secret
    once and then call it to always get the latest value.

    This is useful for Django settings, where values are only evaluated once at
    startup.

    Examples:
    ```
    ### In settings.py
    from codeforlife.settings import LatestSecret

    API_KEY = LatestSecret(name="API_KEY", default="a")  # Define once.

    ### In your code
    from django.conf import settings

    # Always returns the latest value.
    # If the secret does not exist, it returns the default value "a".
    value = settings.API_KEY()

    # You can also override the default value at call time.
    # If the secret does not exist, it returns the default value "b".
    value = settings.API_KEY(default="b")

    # You can also bypass the cache to get the latest value directly from GCP.
    value = settings.API_KEY(cache=False)
    ```
    """

    def __init__(self, name: str, default: t.Optional[T] = None):
        self.name = name
        self.default = default

    @t.overload
    def __call__(self, default: None = None, cache=True) -> t.Union[str, T]: ...

    @t.overload
    def __call__(self, default: T2, cache=True) -> t.Union[str, T2]: ...

    def __call__(self, default: t.Optional[T2] = None, cache=True):
        return get_secret(
            name=self.name,
            default=t.cast(T, self.default) if default is None else default,
            version="latest",
            cache=cache,
        )


# pylint: disable-next=too-few-public-methods
class TypedLatestSecret(LatestSecret[T], t.Generic[T, T2]):
    """A `LatestSecret` that also casts the secret value to a specific type."""

    @t.overload
    def __init__(
        self,
        name: str,
        cast: t.Callable[[str], T],
        default: t.Optional[T2] = None,
    ): ...

    @t.overload
    def __init__(self, name: str, cast: t.Callable[[str], T], default: T): ...

    def __init__(
        self,
        name: str,
        cast: t.Callable[[str], T],
        default: t.Optional[t.Union[T, T2]] = None,
    ):
        super().__init__(name=name, default=t.cast(t.Optional[T], default))

        self.cast = cast

    @t.overload  # type: ignore[override]
    def __call__(self, default: None = None, cache=True) -> t.Union[T, T2]: ...

    @t.overload
    # pylint: disable-next=signature-differs
    def __call__(self, default: T, cache=True) -> T: ...

    def __call__(self, default: t.Optional[T] = None, cache=True):
        secret = super().__call__(default=default, cache=cache)

        # If the secret is None, default, or self.default, return it as-is
        # without casting.
        return (
            t.cast(t.Union[T, T2], secret)
            if secret is None or not isinstance(secret, str)
            else self.cast(secret)
        )
