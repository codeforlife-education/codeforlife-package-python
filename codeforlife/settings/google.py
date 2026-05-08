"""
© Ocado Group
Created on 19/01/2026 at 09:54:59(+00:00).

This file contains all the variables required by Google Cloud Platform (GCP).
"""

import os

from ._secrets import LatestSecret

# pylint: disable=invalid-name

# Our Google OAuth 2.0 client credentials
# https://console.cloud.google.com/auth/clients
GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "354656325390-o5n12nbaivhi4do8lalkh29q403uu9u4.apps.googleusercontent.com",
)
GOOGLE_CLIENT_SECRET = LatestSecret("GOOGLE_CLIENT_SECRET", "REPLACE_ME")

# The ID of our GCP project.
GOOGLE_CLOUD_PROJECT_ID = os.getenv(
    "GOOGLE_CLOUD_PROJECT_ID", "decent-digit-629"
)

# Key management service (KMS)
# https://docs.cloud.google.com/python/docs/reference/cloudkms/latest/summary_overview

GCP_KMS_KEY_RING_LOCATION = LatestSecret(
    "GCP_KMS_KEY_RING_LOCATION", "REPLACE_ME"
)
GCP_KMS_KEY_RING_NAME = LatestSecret("GCP_KMS_KEY_RING_NAME", "REPLACE_ME")
GCP_KMS_KEY_NAME = LatestSecret("GCP_KMS_KEY_NAME", "REPLACE_ME")


def GCP_KMS_KEY_URI() -> str:
    """The URI of the KMS key encryption key (KEK)."""
    return (
        "gcp-kms://"
        f"projects/{GOOGLE_CLOUD_PROJECT_ID}/"
        f"locations/{GCP_KMS_KEY_RING_LOCATION()}/"
        f"keyRings/{GCP_KMS_KEY_RING_NAME()}/"
        f"cryptoKeys/{GCP_KMS_KEY_NAME()}"
    )
