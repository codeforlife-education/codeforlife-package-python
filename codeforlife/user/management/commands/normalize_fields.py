"""
© Ocado Group
Created on 20/05/2026 at 15:44:33(+01:00).
"""

import typing as t
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from threading import Lock

from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Manager, Model, Q, QuerySet

from ....models.fields import BaseEncryptedField, Sha256Field
from ....pprint import PrettyPrinter

LogFn: t.TypeAlias = t.Callable[[str], None]
ModelClass: t.TypeAlias = t.Type[Model]
ModelManager: t.TypeAlias = Manager[Model]
ModelQuerySet: t.TypeAlias = QuerySet[Model]

# pylint: disable=duplicate-code,too-many-locals,import-outside-toplevel,too-many-positional-arguments,too-many-arguments


@dataclass
class HashUniquenessState:
    """
    State to track used hashes and suffixes for ensuring uniqueness when
    normalizing hash fields.
    """

    used_hashes: set[str]
    suffix_counters: dict[str, int]


class Command(BaseCommand):
    """
    Django management command to set encrypted and hash field values for all
    models.
    """

    help = "Normalize encrypted and hash fields for all user models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=1000,
            help="The number of records to process in each batch.",
        )
        parser.add_argument(
            "--enable-threading",
            action="store_true",
            help=(
                "Enable threaded processing where each worker handles a "
                "chunk of rows."
            ),
        )
        parser.add_argument(
            "--max-workers",
            type=int,
            default=4,
            help="Maximum thread workers when --enable-threading is used.",
        )
        parser.add_argument(
            "--disable-styles",
            action="store_true",
            help="Disable styled output.",
        )

    # Define all models and their fields to process
    MODELS_TO_PROCESS = {
        "User": {
            "fields": ["first_name", "last_name", "username", "email"],
            "filter": Q(is_active=True),
        },
        "School": {
            "fields": ["name"],
            "filter": Q(is_active=True),
        },
        "Class": {
            "fields": ["name", "access_code"],
            "filter": Q(
                is_active=True,
                teacher__isnull=False,
                teacher__school__isnull=False,
                teacher__school__is_active=True,
            ),
        },
        "SchoolTeacherInvitation": {
            "fields": [
                "token",
                "invited_teacher_first_name",
                "invited_teacher_last_name",
                "invited_teacher_email",
            ],
            "filter": Q(
                is_active=True,
                school__isnull=False,
                school__is_active=True,
            ),
        },
    }

    def handle(self, *args, **options):
        chunk_size: int = options["chunk_size"]
        enable_threading: bool = options["enable_threading"]
        max_workers: int = options["max_workers"]
        disable_styles: bool = options["disable_styles"]

        if chunk_size < 1:
            raise ValueError("--chunk-size must be at least 1.")

        if max_workers < 1:
            raise ValueError("--max-workers must be at least 1.")

        if max_workers > 8:
            raise ValueError("--max-workers must be <= 8.")

        pprint = PrettyPrinter(
            write=self.stderr.write,
            name=self.__module__,
            disable_styles=disable_styles,
        )

        with pprint.process("Normalizing encrypted fields") as root_pprint:
            for model_name, config in self.MODELS_TO_PROCESS.items():
                fields = t.cast(list[str], config["fields"])
                qs_filter = t.cast(Q | None, config.get("filter"))

                with root_pprint.process(
                    f"Model: {root_pprint.notice.apply(model_name)}"
                ) as model_pprint:
                    for field_name in fields:
                        with model_pprint.process(
                            "Field: " + model_pprint.notice.apply(field_name)
                        ) as field_pprint:
                            self._normalize_field_for_model(
                                model_name=model_name,
                                field_name=field_name,
                                qs_filter=qs_filter,
                                chunk_size=chunk_size,
                                enable_threading=enable_threading,
                                max_workers=max_workers,
                                log=field_pprint,
                            )

        self.stdout.write(
            self.style.SUCCESS("Successfully normalized all configured fields!")
        )

    def _get_model_class(self, model_name: str) -> ModelClass | None:
        from codeforlife.user import models

        try:
            return t.cast(ModelClass, getattr(models, model_name))
        except AttributeError:
            self.stderr.write(
                self.style.ERROR(
                    f"Model '{model_name}' not found in codeforlife.user.models"
                )
            )
            return None

    def _build_plain_field_filter(self, field_name: str) -> tuple[str, Q]:
        plain_field_name = f"_{field_name}_plain"
        plain_field_is_null_or_empty = Q(
            **{f"{plain_field_name}__isnull": True}
        ) | Q(**{f"{plain_field_name}": ""})
        return plain_field_name, plain_field_is_null_or_empty

    def _discover_target_fields(
        self,
        model_class: ModelClass,
        field_name: str,
    ) -> tuple[BaseEncryptedField[t.Any] | None, Sha256Field | None]:
        # Discover related encrypted/hash fields for this plaintext field.
        enc_field_name = f"_{field_name}_enc"
        try:
            enc_field = model_class._meta.get_field(enc_field_name)
            assert isinstance(enc_field, BaseEncryptedField), (
                f"Expected '{model_class.__name__}.{enc_field_name}' to be a "
                f"BaseEncryptedField, got {type(enc_field).__name__}."
            )
            enc_field = t.cast(BaseEncryptedField[t.Any], enc_field)
        except FieldDoesNotExist:
            enc_field = None

        hash_field_name = f"_{field_name}_hash"
        try:
            hash_field = model_class._meta.get_field(hash_field_name)
            assert isinstance(hash_field, Sha256Field), (
                f"Expected '{model_class.__name__}.{hash_field_name}' to be "
                f"a Sha256Field, got {type(hash_field).__name__}."
            )
            hash_field = t.cast(Sha256Field, hash_field)
        except FieldDoesNotExist:
            hash_field = None

        return (enc_field, hash_field)

    def _reset_missing_plain_values(
        self,
        model_manager: ModelManager,
        plain_field_is_null_or_empty: Q,
        enc_field: BaseEncryptedField[t.Any] | None,
        hash_field: Sha256Field | None,
        log: LogFn,
        plain_field_name: str,
    ) -> None:
        update_kwargs: dict[str, t.Any] = {}
        if enc_field is not None:
            update_kwargs[enc_field.name] = b""
        if hash_field is not None:
            update_kwargs[hash_field.name] = ""

        update_count = model_manager.filter(
            plain_field_is_null_or_empty
        ).update(**update_kwargs)
        log(f"Updated {update_count} records with empty {plain_field_name}.")

    def _build_hash_queryset(
        self,
        model_manager: ModelManager,
        plain_field_is_null_or_empty: Q,
        qs_filter: Q | None,
    ) -> ModelQuerySet:
        queryset = model_manager.filter(~plain_field_is_null_or_empty)
        if qs_filter is not None:
            queryset = queryset.filter(qs_filter)
        return t.cast(ModelQuerySet, queryset.order_by("pk"))

    def _normalize_field_for_model(
        self,
        model_name: str,
        field_name: str,
        qs_filter: Q | None = None,
        chunk_size: int = 1000,
        enable_threading: bool = False,
        max_workers: int = 4,
        log: LogFn | None = None,
    ) -> None:
        """Set encrypted and hash field values for a model field."""
        log = log or self.stdout.write

        model_class = self._get_model_class(model_name)
        if model_class is None:
            return

        model_manager = t.cast(
            ModelManager, model_class.objects  # type: ignore[attr-defined]
        )

        plain_field_name, plain_field_is_null_or_empty = (
            self._build_plain_field_filter(field_name)
        )
        enc_field, hash_field = self._discover_target_fields(
            model_class, field_name
        )

        # If neither encrypted nor hash field exists, skip this field.
        if enc_field is None and hash_field is None:
            log(
                f"Skipping {model_name}.{field_name}: no encrypted or hash"
                " field found."
            )
            return

        self._reset_missing_plain_values(
            model_manager=model_manager,
            plain_field_is_null_or_empty=plain_field_is_null_or_empty,
            enc_field=enc_field,
            hash_field=hash_field,
            log=log,
            plain_field_name=plain_field_name,
        )

        # If the hash field does not exist, we don't need to do anything else.
        if hash_field is None:
            log("No hash field found, skipping hash normalization.")
            return

        # If the hash field has no normalization method, there's nothing to do.
        if hash_field.normalize is None:
            log("No normalization method on hash field, skipping.")
            return

        queryset = self._build_hash_queryset(
            model_manager=model_manager,
            plain_field_is_null_or_empty=plain_field_is_null_or_empty,
            qs_filter=qs_filter,
        )

        count = queryset.count()
        if count == 0:
            log(f"No records to hash for {plain_field_name}.")
            return

        log(f"Hashing {count} records...")

        state: HashUniquenessState | None = None
        if model_name in ["School"]:
            # Ensure we avoid collisions with hashes that already exist in rows
            # outside the queryset currently being normalized.
            state = self._build_hash_uniqueness_state(
                model_manager=model_manager,
                model_queryset=queryset,
                hash_field=t.cast(Sha256Field, hash_field),
            )

        if enable_threading and state is not None:
            log(
                "Uniqueness suffix updates require sequential saves; "
                "disabling threading."
            )

        if enable_threading and state is None:
            self._normalize_and_hash_queryset_threaded(
                model_manager=model_manager,
                model_queryset=queryset,
                plain_field_name=plain_field_name,
                enc_field=enc_field,
                hash_field=t.cast(Sha256Field, hash_field),
                count=count,
                chunk_size=chunk_size,
                max_workers=max_workers,
                state=state,
                log=log,
            )
        else:
            self._normalize_and_hash_queryset_sequential(
                model_queryset=queryset,
                plain_field_name=plain_field_name,
                enc_field=enc_field,
                hash_field=t.cast(Sha256Field, hash_field),
                count=count,
                chunk_size=chunk_size,
                state=state,
                log=log,
            )

        log(f"Completed hashing for {field_name}: {count} records.")

    def _bulk_update_batch(
        self,
        model_manager: ModelManager,
        batch: list[Model],
        update_fields: list[str],
        chunk_size: int,
    ) -> int:
        # Ensure this thread has a valid Django DB connection state.
        close_old_connections()

        model_manager.bulk_update(
            batch,
            fields=update_fields,
            batch_size=chunk_size,
        )
        close_old_connections()
        return len(batch)

    def _build_hash_uniqueness_state(
        self,
        model_manager: ModelManager,
        model_queryset: ModelQuerySet,
        hash_field: Sha256Field,
    ) -> HashUniquenessState:
        hash_field_name = hash_field.name
        queryset_ids = model_queryset.values("pk")
        existing_hashes = set(
            model_manager.exclude(pk__in=queryset_ids)
            .exclude(**{f"{hash_field_name}__isnull": True})
            .exclude(**{hash_field_name: ""})
            .values_list(hash_field_name, flat=True)
        )
        return HashUniquenessState(
            used_hashes=existing_hashes,
            suffix_counters={},
        )

    def _assign_unique_plain_and_hash(
        self,
        instance: Model,
        plain_field_name: str,
        enc_field: BaseEncryptedField[t.Any] | None,
        hash_field: Sha256Field,
        state: HashUniquenessState | None,
    ) -> list[str]:
        assert hash_field.normalize is not None
        hash_field_name = hash_field.name
        value = t.cast(str, getattr(instance, plain_field_name))
        normalized_base = hash_field.normalize(value)
        update_fields = [hash_field_name]

        if state is None:
            setattr(
                instance, hash_field_name, Sha256Field.hash(normalized_base)
            )
            return update_fields

        suffix = state.suffix_counters.get(normalized_base, 0)
        while True:
            suffix += 1
            candidate_hash_plain = (
                normalized_base
                if suffix == 1
                else f"{normalized_base} {suffix}"
            )
            candidate_hash = Sha256Field.hash(
                hash_field.normalize(candidate_hash_plain)
            )
            if candidate_hash not in state.used_hashes:
                break

        state.suffix_counters[normalized_base] = suffix
        state.used_hashes.add(candidate_hash)
        setattr(instance, hash_field_name, candidate_hash)
        if suffix == 1:
            return update_fields

        candidate_plain_value = f"{value} {suffix}"
        setattr(instance, plain_field_name, candidate_plain_value)
        update_fields.append(plain_field_name)

        if enc_field is not None:
            BaseEncryptedField.set(
                instance,
                candidate_plain_value,
                enc_field.name,
                normalize=True,
            )
            update_fields.append(enc_field.name)

        return update_fields

    def _normalize_and_hash_queryset_sequential(
        self,
        model_queryset: ModelQuerySet,
        plain_field_name: str,
        enc_field: BaseEncryptedField[t.Any] | None,
        hash_field: Sha256Field,
        count: int,
        chunk_size: int,
        state: HashUniquenessState | None,
        log: LogFn,
    ) -> None:
        hash_field_name = hash_field.name
        only_fields = [plain_field_name, hash_field_name]
        if state is not None:
            only_fields.append("dek")
            if enc_field is not None:
                only_fields.append(enc_field.name)

        for i, instance in enumerate(
            model_queryset.only(*only_fields).iterator(chunk_size),
            start=1,
        ):
            instance_update_fields = self._assign_unique_plain_and_hash(
                instance=instance,
                plain_field_name=plain_field_name,
                enc_field=enc_field,
                hash_field=hash_field,
                state=state,
            )
            instance.save(update_fields=instance_update_fields)
            log(f"Progress: {i}/{count}")

    def _normalize_and_hash_queryset_threaded(
        self,
        model_manager: ModelManager,
        model_queryset: ModelQuerySet,
        plain_field_name: str,
        enc_field: BaseEncryptedField[t.Any] | None,
        hash_field: Sha256Field,
        count: int,
        chunk_size: int,
        max_workers: int,
        state: HashUniquenessState | None,
        log: LogFn,
    ) -> None:
        progress_lock = Lock()
        processed_count = 0
        submitted_batches = 0
        max_pending_futures = max_workers * 2
        hash_field_name = hash_field.name
        update_fields = [hash_field_name]

        def complete_one(future: Future[int]):
            nonlocal processed_count
            processed_batch_size = future.result()
            with progress_lock:
                processed_count += processed_batch_size
                log(f"Progress: {processed_count}/{count}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            pending_futures: set[Future[int]] = set()

            ordered_queryset = model_queryset.only(
                plain_field_name, hash_field_name
            )
            batch: list[Model] = []
            for instance in ordered_queryset.iterator(chunk_size):
                self._assign_unique_plain_and_hash(
                    instance=instance,
                    plain_field_name=plain_field_name,
                    enc_field=enc_field,
                    hash_field=hash_field,
                    state=state,
                )
                batch.append(instance)
                if len(batch) < chunk_size:
                    continue

                pending_futures.add(
                    executor.submit(
                        self._bulk_update_batch,
                        model_manager,
                        batch,
                        update_fields,
                        chunk_size,
                    )
                )
                batch = []
                submitted_batches += 1

                if len(pending_futures) >= max_pending_futures:
                    done, pending_futures = wait(
                        pending_futures,
                        return_when=FIRST_COMPLETED,
                    )
                    for future in done:
                        complete_one(future)

            if batch:
                pending_futures.add(
                    executor.submit(
                        self._bulk_update_batch,
                        model_manager,
                        batch,
                        update_fields,
                        chunk_size,
                    )
                )
                submitted_batches += 1

            if submitted_batches == 0:
                return

            for future in pending_futures:
                complete_one(future)
