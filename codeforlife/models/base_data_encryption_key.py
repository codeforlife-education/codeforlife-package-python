"""
© Ocado Group
Created on 26/01/2026 at 10:32:18(+00:00).

This abstract model brings the `EncryptedModel` and `DataEncryptionKeyField`
together. It also implements the `dek_aead` property, which retrieves and caches
the decrypted DEK's AEAD primitive for use in encryption/decryption operations.
"""

import typing as t

from cachetools import TTLCache
from django.core import checks
from django.core.exceptions import FieldDoesNotExist, ValidationError

from ..encryption import create_dek, get_dek_aead
from ..types import KwArgs
from .encrypted import EncryptedModel
from .utils import is_real_model_class

if t.TYPE_CHECKING:
    from django_stubs_ext.db.models import TypedModelMeta
    from tink.aead import Aead  # type: ignore[import]

    from .fields.data_encryption_key import Dek
else:
    TypedModelMeta = object

AnyBaseDataEncryptionKeyModel = t.TypeVar(
    "AnyBaseDataEncryptionKeyModel", bound="BaseDataEncryptionKeyModel"
)


class BaseDataEncryptionKeyModel(EncryptedModel):
    """Model to store and manage a data encryption key."""

    # Cache configuration for data encryption keys.
    dek_aead_cache_maxsize: float = 1024
    dek_aead_cache_ttl: float = 900  # 15 minutes

    # In-memory cache for the decrypted DEK AEAD primitive.
    DEK_AEAD_CACHE: TTLCache
    # A class-level reference to the DataEncryptionKeyField instance.
    # This is set by the `contribute_to_class` method of the field.
    DEK_FIELD: str

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.DEK_AEAD_CACHE = TTLCache(
            maxsize=cls.dek_aead_cache_maxsize, ttl=cls.dek_aead_cache_ttl
        )

    class Meta(TypedModelMeta):
        abstract = True

    # pylint: disable-next=too-few-public-methods
    class Manager(
        EncryptedModel.Manager[AnyBaseDataEncryptionKeyModel],
        t.Generic[AnyBaseDataEncryptionKeyModel],
    ):
        """Base manager for models with a data encryption key."""

        def _inject_dek_kwarg(self, kwargs: KwArgs):
            """Inject a DEK into the kwargs."""
            kwargs[self.model.DEK_FIELD] = create_dek()

        def create(self, **kwargs):
            """Ensure a DEK is created for new instances."""
            self._inject_dek_kwarg(kwargs)
            return super().create(**kwargs)

    base_manager_class = Manager

    @classmethod
    def _check_dek_field(cls):
        """
        Check that the DEK_FIELD is defined correctly and exists on the model.
        """
        errors: t.List[checks.Error] = []

        # Skip non-real models.
        if not is_real_model_class(cls):
            return errors

        if not hasattr(cls, "DEK_FIELD"):
            errors.append(
                checks.Error(
                    f"'{cls.__module__}.{cls.__name__}' must have DEK_FIELD "
                    "defined.",
                    hint="Set `dek = DataEncryptionKeyField()` on the model.",
                    obj=cls,
                    id="base_data_encryption_key.E001",
                )
            )
        elif not isinstance(cls.DEK_FIELD, str):
            errors.append(
                checks.Error(
                    f"'{cls.__module__}.{cls.__name__}' DEK_FIELD must be a "
                    "string.",
                    hint="Set `dek = DataEncryptionKeyField()` on the model.",
                    obj=cls,
                    id="base_data_encryption_key.E002",
                )
            )
        elif not cls.DEK_FIELD:
            errors.append(
                checks.Error(
                    f"'{cls.__module__}.{cls.__name__}' DEK_FIELD cannot be "
                    "empty.",
                    hint="Set `dek = DataEncryptionKeyField()` on the model.",
                    obj=cls,
                    id="base_data_encryption_key.E003",
                )
            )
        else:
            try:
                cls._meta.get_field(cls.DEK_FIELD)
            except FieldDoesNotExist:
                errors.append(
                    checks.Error(
                        f"'{cls.__module__}.{cls.__name__}' DEK_FIELD "
                        f"'{cls.DEK_FIELD}' does not exist.",
                        hint="Set `dek = DataEncryptionKeyField()` on the "
                        "model.",
                        obj=cls,
                        id="base_data_encryption_key.E004",
                    )
                )

        return errors

    @classmethod
    def check(cls, **kwargs):
        """Run model checks, including custom checks for encrypted models."""
        errors = super().check(**kwargs)
        errors.extend(cls._check_dek_field())

        return errors

    @property
    def dek_aead(self):
        """
        Provides the AEAD primitive for the DEK, caching it for performance.
        """
        # Get the DEK and return None if it's not set.
        dek: t.Optional["Dek"] = getattr(self, self.DEK_FIELD)
        if dek is None:
            raise ValidationError(
                "Cannot retrieve the AEAD primitive for the data encryption "
                "key (DEK) because the DEK is None.",
                code="dek_is_none",
            )

        # Check the cache for the DEK AEAD.
        if self.pk is not None and self.pk in self.DEK_AEAD_CACHE:
            dek_aead = t.cast(
                t.Optional["Aead"], self.DEK_AEAD_CACHE.get(self.pk, None)
            )
            if dek_aead is not None:
                return dek_aead

        # Get the AEAD primitive for the data encryption key.
        dek_aead = get_dek_aead(bytes(dek))

        # Cache the DEK AEAD for future access.
        if self.pk is not None:
            self.DEK_AEAD_CACHE[self.pk] = dek_aead

        return dek_aead

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        # Lazily create a new DEK for new instances.
        if self.pk is None and getattr(self, self.DEK_FIELD) is None:
            self.__dict__[self.DEK_FIELD] = create_dek()

        # pylint: disable=duplicate-code
        return super().save(  # type: ignore[misc]
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        # pylint: enable=duplicate-code
