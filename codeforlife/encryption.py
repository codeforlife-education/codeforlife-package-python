"""
© Ocado Group
Created on 19/01/2026 at 09:55:44(+00:00).

Here we provide a few utility functions that interact with Google Cloud KMS and
the `tink` cryptography library.

To avoid a dependency on Google Cloud KMS during local development and in CI/CD
pipelines, we use fake (mock) implementations of the KMS client and its AEAD
primitive. A simple check for the environment (e.g., `settings.ENV == "local"`)
determines whether to use the real `GcpKmsClient` or a `FakeGcpKmsClient`.

The fake client mimics the behavior of the real one while still using a real
AEAD algorithm locally. `FakeAead` uses `AESGCM` with random nonces and
associated data support, then prefixes the resulting blob so local ciphertext
can be identified as fake-KMS output. This keeps local behavior close to cloud
execution while avoiding cloud credentials.

While the `FakeAead` and `FakeGcpKmsClient` are sufficient for running a local
development server, they are not `unittest.mock.MagicMock` instances by default.
This is intentional, as we don't want the overhead of tracking function calls
during local development.

For unit tests, where you might need to assert that encryption or decryption
methods were called, both fake classes provide an `as_mock()` class method. This
method returns a `MagicMock` instance of the class, allowing you to use mock
assertions like `assert_called_once()`.
"""

import typing as t
from functools import cache
from io import BytesIO
from os import urandom
from unittest.mock import MagicMock, create_autospec

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from tink import (  # type: ignore[import-untyped]
    BinaryKeysetReader,
    BinaryKeysetWriter,
    new_keyset_handle,
    read_keyset_handle,
)
from tink.aead import Aead, aead_key_templates  # type: ignore[import-untyped]
from tink.aead import register as aead_register  # type: ignore[import-untyped]
from tink.integration import gcpkms  # type: ignore[import-untyped]

# Shortcut to the real GcpKmsClient class.
_GcpKmsClient = gcpkms.GcpKmsClient


class FakeAead:
    """A fake AEAD primitive for local testing."""

    ciphertext_prefix = b"fake_enc:"
    nonce_size = 12

    def __init__(self, key: bytes):
        self._aesgcm = AESGCM(key)

    def encrypt(self, plaintext: bytes, associated_data: bytes):
        """Encrypt data using AES-GCM and return a prefixed blob."""
        nonce = urandom(self.nonce_size)
        ciphertext = self._aesgcm.encrypt(
            nonce=nonce,
            data=plaintext,
            associated_data=associated_data,
        )

        return self.ciphertext_prefix + nonce + ciphertext

    def decrypt(self, ciphertext: bytes, associated_data: bytes):
        """Decrypt a prefixed AES-GCM blob."""
        if not ciphertext.startswith(self.ciphertext_prefix):
            raise ValueError("Invalid ciphertext for fake mock")
        ciphertext = ciphertext.removeprefix(self.ciphertext_prefix)

        return self._aesgcm.decrypt(
            nonce=ciphertext[: self.nonce_size],
            data=ciphertext[self.nonce_size :],
            associated_data=associated_data,
        )

    def as_mock(self):
        """
        Returns the class as a functional MagicMock for testing. The mock tracks
        calls while still performing the fake encryption and decryption by using
        the original methods as side effects. We set `instance=True` to ensure
        the mock behaves as an instance of the class, not the class itself.
        """
        mock: MagicMock = create_autospec(Aead, instance=True)
        mock.encrypt.side_effect = self.encrypt
        mock.decrypt.side_effect = self.decrypt

        return mock


class FakeGcpKmsClient:
    """A fake GcpKmsClient for local testing."""

    # Fake key encryption key (KEK) for local testing.
    # pylint: disable-next=line-too-long
    kek = b"fake_kek:\xba\xcc\x8c;\xa9\x85k\n\x93\xb7\x1b2\xab\x86\x9d\xea\xb1+\x88\xc0\xc4y3"

    def __init__(self, key_uri: str):
        self.key_uri = key_uri

    @staticmethod
    def register_client(
        key_uri: t.Optional[str], credentials_path: t.Optional[str]
    ):
        """No-op for registering the fake client."""

    # pylint: disable-next=unused-argument
    def get_aead(self, key_uri: str) -> Aead:
        """Return the fake AEAD primitive."""
        return FakeAead(self.kek)

    @classmethod
    def as_mock(cls):
        """
        Returns the class as a functional MagicMock for testing. It returns a
        mocked FakeAead instance that is also functional. We set `instance=True`
        to ensure the mock behaves as an instance of the class, not the class
        itself.
        """
        mock: MagicMock = create_autospec(_GcpKmsClient, instance=True)
        mock.get_aead.return_value = FakeAead(cls.kek).as_mock()

        return mock


@cache
def _get_kek_aead():
    """Get the AEAD primitive for the key encryption key (KEK)."""
    return GcpKmsClient(key_uri=settings.GCP_KMS_KEY_URI()).get_aead(
        key_uri=settings.GCP_KMS_KEY_URI()
    )


def create_dek():
    """
    Creates a new random AES-256-GCM data encryption key (DEK), wraps it with
    Cloud KMS, and returns the binary blob for storage.
    """
    # In local environment, return a fake encrypted DEK.
    if settings.ENV == "local":
        return _get_kek_aead().encrypt(urandom(32), b"")

    stream = BytesIO()
    new_keyset_handle(key_template=aead_key_templates.AES256_GCM).write(
        keyset_writer=BinaryKeysetWriter(stream),
        master_key_primitive=_get_kek_aead(),
    )

    return stream.getvalue()


def get_dek_aead(dek: bytes) -> Aead:
    """
    Takes an encrypted DEK, decrypts it with the KEK, and returns the AEAD
    primitive for performing cryptographic operations.
    """
    if not dek:
        raise ValueError("The data encryption key (DEK) is missing.")

    # In local environment, return the fake AEAD primitive.
    if settings.ENV == "local":
        return FakeAead(_get_kek_aead().decrypt(dek, b""))

    return read_keyset_handle(
        keyset_reader=BinaryKeysetReader(dek),
        master_key_aead=_get_kek_aead(),
    ).primitive(Aead)


# Ensure Tink AEAD is registered.
aead_register()

# Use the fake client in 'local' environment, otherwise use the real one.
GcpKmsClient = FakeGcpKmsClient if settings.ENV == "local" else _GcpKmsClient

# Register the GCP KMS client with Tink.
GcpKmsClient.register_client(
    key_uri=settings.GCP_KMS_KEY_URI(), credentials_path=None
)
