"""
© Ocado Group
Created on 11/08/2025 at 11:07:45(+01:00).
"""

import typing as t

import requests
from django.conf import settings

from ...caches import BaseDynamicKeyCache
from ...types import OAuth2TokenFromRefreshDict
from ..models import GoogleUser

GoogleOAuth2TokenCacheKey = int


class GoogleOAuth2TokenCacheValue(t.TypedDict):
    """A cached OAuth 2.0 token from Google."""

    access_token: str
    token_type: str
    scope: str


class GoogleOAuth2TokenCache(
    BaseDynamicKeyCache[GoogleOAuth2TokenCacheKey, GoogleOAuth2TokenCacheValue]
):
    """
    Authorization to a user's Google account. The key is the user's ID. The
    value is the user's access-token. If the user does not have a cached
    access-token but does have a refresh-token stored in the database, an
    access-token will automatically be retrieved and cached for the user.
    """

    # Shorthand for convenience.
    Key: t.TypeAlias = GoogleOAuth2TokenCacheKey
    Value: t.TypeAlias = GoogleOAuth2TokenCacheValue

    @staticmethod
    def make_key(key):
        return f"{key}.google.access_token"

    @classmethod
    def get(cls, key, default=None, version=None):
        value = super().get(key, default, version)
        if not value:
            user_queryset = GoogleUser.objects.filter(id=key)
            if user_queryset.exists():
                user = user_queryset.get()

                response = requests.post(
                    url="https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": user.userprofile.google_refresh_token,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET(),
                    },
                    timeout=10,
                )
                if response.ok:
                    token: OAuth2TokenFromRefreshDict = response.json()
                    expires_in = token["expires_in"]
                    del token["expires_in"]  # type: ignore[misc]
                    value = t.cast(GoogleOAuth2TokenCacheValue, token)

                    # -3 seconds to reduce likeliness of using an expired token.
                    cls.set(key=key, value=value, timeout=expires_in - 3)

        return value

    @classmethod
    def get_auth_header(
        cls, key: GoogleOAuth2TokenCacheKey, default=None, version=None
    ):
        """
        Get a Google OAuth 2.0 token in the form of an Authorization header.
        """
        value = cls.get(key, default, version)
        if value:
            return f"{value['token_type']} {value['access_token']}"

        return None
