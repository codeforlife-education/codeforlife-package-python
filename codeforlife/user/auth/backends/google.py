"""
© Ocado Group
Created on 01/07/2025 at 12:48:13(+01:00).
"""

import typing as t
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from ....request import HttpRequest
from ....types import OAuth2TokenFromCodeDict
from ...caches import GoogleOAuth2TokenCache
from ...models import GoogleUser
from .base import BaseBackend


class GoogleBackend(BaseBackend):
    """Authenticate a user using the code returned by Google's callback URL."""

    user_class = GoogleUser

    # pylint: disable-next=too-many-locals
    def authenticate(  # type: ignore[override]
        self,
        request: t.Optional[HttpRequest],
        code: t.Optional[str] = None,
        code_verifier: t.Optional[str] = None,
        redirect_uri: t.Optional[str] = None,
        **kwargs,
    ):
        if code is None or code_verifier is None or redirect_uri is None:
            return None

        # Get user's google-access-token.
        response = requests.post(
            url="https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": redirect_uri,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET(),
                "grant_type": "authorization_code",
            },
            timeout=5,
        )
        token_received_at = timezone.now()
        if not response.ok:
            return None

        token: OAuth2TokenFromCodeDict = response.json()
        if "error" in token:
            return None

        expires_in = token["expires_in"]
        del token["expires_in"]  # type: ignore[misc]
        refresh_token = token["refresh_token"]
        del token["refresh_token"]  # type: ignore[misc]

        user = self.user_class.objects.sync_or_create(
            auth_header=f"{token['token_type']} {token['access_token']}",
            refresh_token=refresh_token,
        )

        GoogleOAuth2TokenCache.set(
            key=user.id,
            value=t.cast(GoogleOAuth2TokenCache.Value, token),
            timeout=(
                token_received_at
                - timezone.now()
                + timedelta(seconds=expires_in)
            ).seconds,
        )

        return user
