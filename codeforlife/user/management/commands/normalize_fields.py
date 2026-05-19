import typing as t

from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Model, Q

from ....models.fields import Sha256Field


class Command(BaseCommand):
    """
    Django management command to set encrypted and hash field values for all models.

    This command replicates the logic from migration 0005_client_side_encryption_part_3
    and automatically processes all models in the codeforlife.user app that have
    encrypted fields.
    """

    help = "Normalize encrypted and hash fields for all user models"

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
        self.stdout.write(
            self.style.SUCCESS("Starting to normalize encrypted fields...")
        )
        self.stdout.write("")

        for model_name, config in self.MODELS_TO_PROCESS.items():
            for field_name in config["fields"]:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f"Processing {model_name}.{field_name}..."
                    )
                )
                self.set_field(model_name, field_name, config.get("filter"))
                self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS("Successfully normalized all encrypted fields!")
        )

    def set_field(
        self, model_name: str, field_name: str, qs_filter: Q | None = None
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
            model_class._meta.get_field(hash_field_name)
            hash_field_exists = True
        except FieldDoesNotExist:
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

        count = queryset.count()
        if count == 0:
            self.stdout.write(f"  No instances to hash for {plain_field_name}")
            return

        self.stdout.write(f"  Hashing {count} instances...")

        # Set the chunk size for bulk updates and initialize an empty list to
        # hold instances to be updated.
        chunk_size = 1000
        instances: list[Model] = []

        # Helper function to bulk update instances in chunks.
        def bulk_update(i: int):
            nonlocal instances
            if not instances:
                return
            manager.bulk_update(
                instances, fields=[hash_field_name], batch_size=chunk_size
            )
            instances = []
            self.stdout.write(f"    Progress: {i}/{count}")

        # Iterate over the queryset in chunks and save each instance.
        i = 0
        for i, instance in enumerate(
            queryset.only(plain_field_name, hash_field_name).iterator(
                chunk_size
            ),
            start=1,
        ):
            # Get the plain value.
            value = getattr(instance, plain_field_name)

            # Set the hash value using the Sha256Field's set method, which will
            # normalize and hash the value before setting it on the instance.
            Sha256Field.set(instance, value, hash_field_name)

            # Append the instance to the list of instances to be bulk updated.
            instances.append(instance)

            # Print progress every chunk_size instances.
            if len(instances) == chunk_size:
                bulk_update(i)

        # Bulk update any remaining instances.
        if len(instances) > 0:
            bulk_update(count)

        self.stdout.write(
            self.style.SUCCESS(
                f"  Successfully hashed {count} instances for {field_name}"
            )
        )
