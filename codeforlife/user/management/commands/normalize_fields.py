import typing as t
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from threading import Lock

from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Model, Q, QuerySet

from ....models.fields import Sha256Field


@dataclass
class HashUniquenessState:
    used_hashes: set[str]
    suffix_counters: dict[str, int]


class Command(BaseCommand):
    """
    Django management command to set encrypted and hash field values for all models.

    This command replicates the logic from migration 0005_client_side_encryption_part_3
    and automatically processes all models in the codeforlife.user app that have
    encrypted fields.
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

        if chunk_size < 1:
            raise ValueError("--chunk-size must be at least 1.")

        if max_workers < 1:
            raise ValueError("--max-workers must be at least 1.")

        if max_workers > 8:
            raise ValueError("--max-workers must be <= 8.")

        self.stdout.write(
            self.style.SUCCESS("Starting to normalize encrypted fields...")
        )
        self.stdout.write("")

        for model_name, config in self.MODELS_TO_PROCESS.items():
            fields = t.cast(list[str], config["fields"])
            qs_filter = t.cast(Q | None, config.get("filter"))

            for field_name in fields:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f"Processing {model_name}.{field_name}..."
                    )
                )
                self.set_field(
                    model_name=model_name,
                    field_name=field_name,
                    qs_filter=qs_filter,
                    chunk_size=chunk_size,
                    enable_threading=enable_threading,
                    max_workers=max_workers,
                )
                self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS("Successfully normalized all encrypted fields!")
        )

    def set_field(
        self,
        model_name: str,
        field_name: str,
        qs_filter: Q | None = None,
        chunk_size: int = 1000,
        enable_threading: bool = False,
        max_workers: int = 4,
    ):
        """Set encrypted and hash field values for a model field."""
        from codeforlife.user import models

        # Get the model class from the apps registry.
        try:
            model_class: t.Type[Model] = getattr(models, model_name)
        except AttributeError:
            self.stderr.write(
                self.style.ERROR(
                    f"Model '{model_name}' not found in codeforlife.user.models"
                )
            )
            return

        manager = model_class.objects  # type: ignore[attr-defined]

        # Generate the plain field name and the Q object to filter instances
        # where the plain field is null or empty.
        plain_field_name = f"_{field_name}_plain"
        plain_field_is_null_or_empty = Q(
            **{f"{plain_field_name}__isnull": True}
        ) | Q(**{f"{plain_field_name}": ""})

        # Generate the encrypted and hash field names and check if they exist.
        enc_field_name = f"_{field_name}_enc"
        try:
            model_class._meta.get_field(enc_field_name)
            enc_field_exists = True
        except FieldDoesNotExist:
            enc_field_exists = False

        hash_field_name = f"_{field_name}_hash"
        try:
            hash_field = t.cast(
                Sha256Field, model_class._meta.get_field(hash_field_name)
            )
            hash_field_exists = True
        except FieldDoesNotExist:
            hash_field = None
            hash_field_exists = False

        # If neither encrypted nor hash field exists, skip this field.
        if not enc_field_exists and not hash_field_exists:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping {model_name}.{field_name}: no encrypted or hash field found"
                )
            )
            return

        # Update instances where the plain field is null or empty, setting the
        # encrypted and hash fields to empty values (if they exist).
        update_kwargs: dict[str, t.Any] = {}
        if enc_field_exists:
            update_kwargs[enc_field_name] = b""
        if hash_field_exists:
            update_kwargs[hash_field_name] = ""

        update_count = manager.filter(plain_field_is_null_or_empty).update(
            **update_kwargs
        )
        self.stdout.write(
            f"  Updated {update_count} instances with null/empty {plain_field_name}"
        )

        # If the hash field does not exist, we don't need to do anything else.
        if not hash_field_exists:
            return

        # Build a queryset of instances where the plain field is not null or
        # empty, and apply any additional filtering provided by qs_filter.
        queryset = manager.filter(~plain_field_is_null_or_empty)
        if qs_filter is not None:
            queryset = queryset.filter(qs_filter)
        queryset = queryset.order_by("pk")

        count = queryset.count()
        if count == 0:
            self.stdout.write(f"  No instances to hash for {plain_field_name}")
            return

        self.stdout.write(f"  Hashing {count} instances...")
        unique_hash_field = bool(t.cast(Sha256Field, hash_field).unique)

        state: HashUniquenessState | None = None
        if unique_hash_field:
            # Ensure we avoid collisions with hashes that already exist in rows
            # outside the queryset currently being normalized.
            state = self._build_hash_uniqueness_state(
                manager=manager,
                queryset=queryset,
                hash_field_name=hash_field_name,
            )

        if enable_threading:
            self._hash_queryset_threaded(
                manager=manager,
                queryset=queryset,
                plain_field_name=plain_field_name,
                hash_field_name=hash_field_name,
                hash_field=t.cast(Sha256Field, hash_field),
                count=count,
                chunk_size=chunk_size,
                max_workers=max_workers,
                state=state,
            )
        else:
            self._hash_queryset(
                manager=manager,
                queryset=queryset,
                plain_field_name=plain_field_name,
                hash_field_name=hash_field_name,
                hash_field=t.cast(Sha256Field, hash_field),
                count=count,
                chunk_size=chunk_size,
                state=state,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"  Successfully hashed {count} instances for {field_name}"
            )
        )

    def _iter_model_batches(self, models: QuerySet[Model], chunk_size: int):
        batch: list[Model] = []
        for model in models.iterator(chunk_size):
            batch.append(model)
            if len(batch) >= chunk_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def _hash_batch(
        self,
        manager,
        batch: list[Model],
        update_fields: list[str],
        chunk_size: int,
    ) -> int:
        # Ensure this thread has a valid Django DB connection state.
        close_old_connections()

        manager.bulk_update(
            batch,
            fields=update_fields,
            batch_size=chunk_size,
        )
        close_old_connections()
        return len(batch)

    def _build_hash_uniqueness_state(
        self,
        manager,
        queryset,
        hash_field_name: str,
    ) -> HashUniquenessState:
        queryset_ids = queryset.values("pk")
        existing_hashes = set(
            manager.exclude(pk__in=queryset_ids)
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
        hash_field_name: str,
        hash_field: Sha256Field,
        state: HashUniquenessState | None,
    ):
        value = t.cast(str, getattr(instance, plain_field_name))
        normalized_base = hash_field.normalize(value)

        if state is None:
            setattr(instance, plain_field_name, normalized_base)
            setattr(
                instance, hash_field_name, Sha256Field.hash(normalized_base)
            )
            return

        suffix = state.suffix_counters.get(normalized_base, 0)
        while True:
            suffix += 1
            candidate_plain = (
                normalized_base
                if suffix == 1
                else f"{normalized_base} {suffix}"
            )
            candidate_hash = Sha256Field.hash(
                hash_field.normalize(candidate_plain)
            )
            if candidate_hash not in state.used_hashes:
                break

        state.suffix_counters[normalized_base] = suffix
        state.used_hashes.add(candidate_hash)
        setattr(instance, plain_field_name, candidate_plain)
        setattr(instance, hash_field_name, candidate_hash)

    def _hash_queryset(
        self,
        manager,
        queryset,
        plain_field_name: str,
        hash_field_name: str,
        hash_field: Sha256Field,
        count: int,
        chunk_size: int,
        state: HashUniquenessState | None,
    ):
        instances: list[Model] = []
        update_fields = [plain_field_name, hash_field_name]

        def bulk_update(i: int):
            nonlocal instances
            if not instances:
                return
            manager.bulk_update(
                instances,
                fields=update_fields,
                batch_size=chunk_size,
            )
            instances = []
            self.stdout.write(f"    Progress: {i}/{count}")

        i = 0
        for i, instance in enumerate(
            queryset.only(plain_field_name, hash_field_name).iterator(
                chunk_size
            ),
            start=1,
        ):
            self._assign_unique_plain_and_hash(
                instance=instance,
                plain_field_name=plain_field_name,
                hash_field_name=hash_field_name,
                hash_field=hash_field,
                state=state,
            )
            instances.append(instance)

            if len(instances) == chunk_size:
                bulk_update(i)

        if len(instances) > 0:
            bulk_update(count)

    def _hash_queryset_threaded(
        self,
        manager,
        queryset,
        plain_field_name: str,
        hash_field_name: str,
        hash_field: Sha256Field,
        count: int,
        chunk_size: int,
        max_workers: int,
        state: HashUniquenessState | None,
    ):
        progress_lock = Lock()
        processed_count = 0
        submitted_batches = 0
        max_pending_futures = max_workers * 2
        update_fields = [plain_field_name, hash_field_name]

        def complete_one(future: Future[int]):
            nonlocal processed_count
            processed_batch_size = future.result()
            with progress_lock:
                processed_count += processed_batch_size
                self.stdout.write(f"    Progress: {processed_count}/{count}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            pending_futures: set[Future[int]] = set()

            models = queryset.only(plain_field_name, hash_field_name)
            batch: list[Model] = []
            for instance in models.iterator(chunk_size):
                self._assign_unique_plain_and_hash(
                    instance=instance,
                    plain_field_name=plain_field_name,
                    hash_field_name=hash_field_name,
                    hash_field=hash_field,
                    state=state,
                )
                batch.append(instance)
                if len(batch) < chunk_size:
                    continue

                pending_futures.add(
                    executor.submit(
                        self._hash_batch,
                        manager,
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
                        self._hash_batch,
                        manager,
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
