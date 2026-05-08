"""
© Ocado Group
Created on 19/06/2025 at 11:30:00(+00:00).
"""

import logging
import typing as t
from datetime import datetime, timedelta

import jwt
import requests
from django.conf import settings
from django.utils import timezone
from jwt.types import JWKDict, Options

from ..types import JsonDict
from .base import BasePermission


class AuthHeaderIsGitHubOidcToken(BasePermission):
    """
    Checks the incoming request has an "Authorization" header that contains a
    GitHub-issued OIDC token.

    https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
    """

    issuer = "https://token.actions.githubusercontent.com"
    jwks_url = f"{issuer}/.well-known/jwks"

    # Cache for GitHub's JSON Web Key Set to avoid fetching on every request.
    _jwks: t.Optional[t.List[JsonDict]] = None
    _jwks_last_fetched: t.Optional[datetime] = None

    def __init__(self, jwks_ttl: int = 3600):
        # pylint: disable=line-too-long
        """Initialize the permission.

        Args:
            jwks_ttl: The time-to-live for GitHub's cached JSON Web Key Set in seconds.
        """
        # pylint: enable=line-too-long
        super().__init__()

        self.jwks_ttl = timedelta(seconds=jwks_ttl)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.jwks_ttl == other.jwks_ttl
        )

    def _get_jwks(self):
        """Fetches GitHub's JSON Web Key Set and caches it."""
        now = timezone.now()

        if (
            self._jwks
            and self._jwks_last_fetched
            and (now - self._jwks_last_fetched) >= self.jwks_ttl
        ):
            return self._jwks

        response = requests.get(self.jwks_url, timeout=5)
        if not response.ok:
            logging.error("Failed to get GitHub's JSON Web Key Set.")
            return None

        self._jwks_last_fetched = now
        self._jwks = response.json()["keys"]
        return self._jwks

    def _decode_token(self, token: str):
        jwks = self._get_jwks()
        if not jwks:
            return None

        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            jwk: t.Optional[JWKDict] = None
            for _jwk in jwks:
                if _jwk.get("kid") == kid:
                    jwk = _jwk
                    break

            if not jwk:
                logging.info("No matching JSON Web Key found for ID: %s", kid)
                return None

            return jwt.decode(
                token,
                key=jwt.PyJWK.from_dict(jwk),
                algorithms=["RS256", "RS384", "RS512"],
                audience=settings.SERVICE_DOMAIN,
                issuer=self.issuer,
                options=Options(require=["exp"], verify_signature=True),
            )

        except jwt.exceptions.ExpiredSignatureError:
            logging.info("JSON Web Token has expired.")
        except jwt.exceptions.InvalidAudienceError:
            logging.info("JSON Web Token audience mismatch.")
        except jwt.exceptions.InvalidIssuerError:
            logging.info("JSON Web Token issuer mismatch.")
        except jwt.exceptions.InvalidSignatureError:
            logging.info("JSON Web Token signature is invalid.")
        except jwt.exceptions.PyJWTError as error:
            logging.info("JSON Web Token verification failed: %s", error)

        return None

    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            if not auth_header.startswith("Bearer "):
                logging.info("Expected a bearer token.")
                return False

            token = auth_header.split(" ")[1]

            decoded_token = self._decode_token(token)
            return decoded_token is not None

        return False
