"""
© Ocado Group
Created on 16/03/2026 at 10:58:04(+00:00).
"""

import typing as t
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from threading import Lock

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import CharField, Field, Model, Q, QuerySet, TextField

from ....encryption import create_dek
from ....models import BaseDataEncryptionKeyModel
from ....models.fields import EncryptedTextField, Sha256Field
from ....models.utils import is_real_model_class
from ....pprint import PrettyPrinter

PlaintextField: t.TypeAlias = t.Union[CharField, TextField]
FieldsToUpdate: t.TypeAlias = t.List[
    t.Tuple[
        PlaintextField,
        t.Optional[EncryptedTextField],
        t.Optional[Sha256Field],
    ]
]


# pylint: disable-next=missing-class-docstring
class Command(BaseCommand):
    format_help = (
        "Arguments should be one or more Django app labels. "
        "For each model in each app, fields ending with '_plain' will be "
        "copied into matching '_enc' and '_hash' fields."
    )
    help = f"Encrypts and hashes plaintext fields for app models. {format_help}"

    def add_arguments(self, parser):
        parser.add_argument(
            "app_labels", nargs="+", type=str, help=self.format_help
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=100,
            help="The number of records to process in each batch.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be updated without writing to the database.",
        )
        parser.add_argument(
            "--disable-styles",
            action="store_true",
            help="Disable styled output.",
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

    # pylint: disable-next=too-many-locals
    def _discover_model_fields(
        self,
        model_class: t.Type[Model],
        pprint: PrettyPrinter,
    ) -> FieldsToUpdate:
        model_spec = (
            f"{model_class._meta.app_label}.{model_class._meta.model_name}"
        )
        plain_fields_by_name = {
            field.name: field
            for field in model_class._meta.fields
            if isinstance(field, (CharField, TextField))
            and field.name.endswith("_plain")
        }

        fields_to_update: FieldsToUpdate = []
        for field_name, plain_field in plain_fields_by_name.items():
            field_name_prefix = field_name[: -len("_plain")]
            enc_field_name = f"{field_name_prefix}_enc"
            hash_field_name = f"{field_name_prefix}_hash"

            enc_field: t.Optional[EncryptedTextField] = None
            hash_field: t.Optional[Sha256Field] = None

            try:
                enc_field_obj = model_class._meta.get_field(enc_field_name)
            except FieldDoesNotExist:
                enc_field_obj = None

            try:
                hash_field_obj = model_class._meta.get_field(hash_field_name)
            except FieldDoesNotExist:
                hash_field_obj = None

            if isinstance(enc_field_obj, EncryptedTextField):
                enc_field = enc_field_obj
            elif enc_field_obj is not None:
                pprint(
                    "Skipping encrypted field due to type mismatch: "
                    + pprint.notice.apply(f"{model_spec}.{enc_field_name}")
                )

            if isinstance(hash_field_obj, Sha256Field):
                hash_field = hash_field_obj
            elif hash_field_obj is not None:
                pprint(
                    "Skipping hash field due to type mismatch: "
                    + pprint.notice.apply(f"{model_spec}.{hash_field_name}")
                )

            if enc_field is None and hash_field is None:
                if enc_field_obj is not None:
                    pprint(
                        "No valid target fields found for: "
                        + pprint.notice.apply(f"{model_spec}.{enc_field_name}")
                    )
                if hash_field_obj is not None:
                    pprint(
                        "No valid target fields found for: "
                        + pprint.notice.apply(f"{model_spec}.{hash_field_name}")
                    )
                continue

            target_fields = ", ".join(
                field_name
                for field_name in (enc_field_name, hash_field_name)
                if (field_name == enc_field_name and enc_field is not None)
                or (field_name == hash_field_name and hash_field is not None)
            )

            pprint(
                "Discovered field mapping: "
                + pprint.notice.apply(f"{field_name} -> {target_fields}")
            )
            fields_to_update.append((plain_field, enc_field, hash_field))

        return fields_to_update

    def _get_model_queryset(
        self,
        model_class: t.Type[Model],
        fields_to_update: FieldsToUpdate,
        pprint: PrettyPrinter,
    ):
        if not fields_to_update:
            pprint("No fields to update.")
            return model_class.objects.none()  # type: ignore[attr-defined]

        models = model_class.objects.all()  # type: ignore[attr-defined]

        # Pre-fetch the fields which will be read.
        only_fields = [
            plain_field.name for plain_field, _, _ in fields_to_update
        ]
        if issubclass(model_class, BaseDataEncryptionKeyModel):
            only_fields.append(model_class.DEK_FIELD)
        models = models.only(*only_fields)

        # Generate a filter for a field that has a null or empty value.
        def null_or_empty(field: Field, empty: t.Any):
            return Q(**{f"{field.name}__isnull": True}) | Q(
                **{field.name: empty}
            )

        # Filter to models where at least one field needs to be updated.
        q = Q()
        for plain_field, enc_field, hash_field in fields_to_update:
            # Exclude models where the plaintext field is null or empty and
            # include models where the encrypted or hash field is null or empty.
            q |= ~null_or_empty(plain_field, "") & (
                null_or_empty(enc_field, b"") | null_or_empty(hash_field, "")
                if enc_field is not None and hash_field is not None
                else (
                    null_or_empty(enc_field, b"")
                    if enc_field is not None
                    else null_or_empty(t.cast(Sha256Field, hash_field), "")
                )
            )
        models = models.filter(q)

        # Exclude inactive records for certain models.
        if model_class._meta.model_name in [
            "school",
            "user",
            "schoolteacherinvitation",
            "class",
        ]:
            models = models.exclude(is_active=False)

        if model_class._meta.model_name == "class":
            models = models.exclude(teacher__isnull=True).exclude(
                teacher__school__isnull=True
            )
        elif model_class._meta.model_name == "schoolteacherinvitation":
            models = models.exclude(school__isnull=True)

        # Exclude default levels, which are shared across users and not
        # encrypted.
        if model_class._meta.model_name == "level":
            models = models.exclude(default=True)

        return models

    def _update_model_instance(
        self,
        model_class: t.Type[Model],
        model: Model,
        fields_to_update: FieldsToUpdate,
    ):
        update_fields: t.List[str] = []

        # If the model uses DEKs and doesn't have one set, create and assign
        # a DEK so that it can be used for encrypting fields.
        if (
            issubclass(model_class, BaseDataEncryptionKeyModel)
            and getattr(model, model_class.DEK_FIELD) is None
        ):
            setattr(model, model_class.DEK_FIELD, create_dek())
            update_fields.append(model_class.DEK_FIELD)

        # Iterate through the fields to update and copy the plaintext value
        # into the encrypted and hash fields as appropriate.
        for plain_field, enc_field, hash_field in fields_to_update:
            plaintext = getattr(model, plain_field.name)
            field_property_name = plain_field.name.removesuffix(
                "_plain"
            ).removeprefix("_")
            setattr(model, field_property_name, plaintext)

            if enc_field is not None:
                update_fields.append(enc_field.name)
            if hash_field is not None:
                update_fields.append(hash_field.name)

        # Save the model with the updated fields.
        model.save(update_fields=update_fields)

    def _iter_model_batches(self, models: QuerySet[Model], chunk_size: int):
        batch: t.List[Model] = []
        for model in models.iterator(chunk_size):
            batch.append(model)
            if len(batch) >= chunk_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def _process_model_batch(
        self,
        model_class: t.Type[Model],
        batch: t.List[Model],
        fields_to_update: FieldsToUpdate,
    ) -> int:
        # Ensure this thread has a valid Django DB connection state.
        close_old_connections()

        for model in batch:
            self._update_model_instance(model_class, model, fields_to_update)

        close_old_connections()
        return len(batch)

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def _update_models(
        self,
        chunk_size: int,
        model_class: t.Type[Model],
        models: QuerySet[Model],
        model_count: int,
        fields_to_update: FieldsToUpdate,
        pprint: PrettyPrinter,
    ):
        for model_index, model in enumerate(models.iterator(chunk_size)):
            # Print progress at the start of each chunk.
            if model_index % chunk_size == 0:
                pprint(f"({model_index}/{model_count})")

            self._update_model_instance(
                model_class=model_class,
                model=model,
                fields_to_update=fields_to_update,
            )

    # pylint: disable-next=too-many-arguments,too-many-locals,too-many-positional-arguments
    def _update_models_threaded(
        self,
        chunk_size: int,
        max_workers: int,
        model_class: t.Type[Model],
        models: QuerySet[Model],
        model_count: int,
        fields_to_update: FieldsToUpdate,
        pprint: PrettyPrinter,
    ):
        progress_lock = Lock()
        processed_count = 0
        submitted_batches = 0
        max_pending_futures = max_workers * 2

        def complete_one(future: Future[int]):
            nonlocal processed_count
            processed_batch_size = future.result()
            with progress_lock:
                processed_count += processed_batch_size
                pprint(f"({processed_count}/{model_count})")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            pending_futures: t.Set[Future[int]] = set()

            for batch in self._iter_model_batches(models, chunk_size):
                pending_futures.add(
                    executor.submit(
                        self._process_model_batch,
                        model_class,
                        batch,
                        fields_to_update,
                    )
                )
                submitted_batches += 1

                if len(pending_futures) >= max_pending_futures:
                    done, pending_futures = wait(
                        pending_futures,
                        return_when=FIRST_COMPLETED,
                    )
                    for future in done:
                        complete_one(future)

            if submitted_batches == 0:
                return

            for future in pending_futures:
                complete_one(future)

    # pylint: disable-next=too-many-locals
    def handle(self, *args, **options):
        app_labels: t.List[str] = options["app_labels"]
        chunk_size: int = options["chunk_size"]
        dry_run: bool = options["dry_run"]
        disable_styles: bool = options["disable_styles"]
        enable_threading: bool = options["enable_threading"]
        max_workers: int = options["max_workers"]

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

        for app_label in set(app_label.lower() for app_label in app_labels):
            with pprint.process(
                f"Processing app: {pprint.notice.apply(app_label)}"
            ) as app_pprint:
                app_config = apps.get_app_config(app_label)

                # Get real model classes.
                model_classes = [
                    model_class
                    for model_class in app_config.get_models()
                    if is_real_model_class(model_class)
                ]

                # Sort model classes so that those saving DEKs are processed
                # first, ensuring that other models with dependencies on DEKs
                # can encrypt their fields.
                model_classes = sorted(
                    model_classes,
                    key=lambda cls: issubclass(cls, BaseDataEncryptionKeyModel),
                    reverse=True,
                )

                for model_class in model_classes:
                    with app_pprint.process(
                        "Processing model: "
                        + app_pprint.notice.apply(model_class._meta.model_name)
                    ) as model_pprint:
                        fields_to_update = self._discover_model_fields(
                            model_class, model_pprint
                        )

                        models = self._get_model_queryset(
                            model_class, fields_to_update, model_pprint
                        )
                        model_count = models.count()

                        if dry_run:
                            model_pprint(
                                f"Dry run: would update {model_count} records."
                            )
                            continue

                        if model_count == 0:
                            model_pprint("No models to update.")
                            continue

                        if enable_threading:
                            self._update_models_threaded(
                                chunk_size=chunk_size,
                                max_workers=max_workers,
                                model_class=model_class,
                                models=models,
                                model_count=model_count,
                                fields_to_update=fields_to_update,
                                pprint=model_pprint,
                            )
                        else:
                            self._update_models(
                                chunk_size=chunk_size,
                                model_class=model_class,
                                models=models,
                                model_count=model_count,
                                fields_to_update=fields_to_update,
                                pprint=model_pprint,
                            )
