import typing as t

from django.apps.registry import Apps
from django.core.exceptions import FieldDoesNotExist
from django.db import migrations
from django.db.models import CharField, Model, Q

from ...models.fields import EncryptedTextField, Sha256Field


def set_field(model_name: str, field_name: str, qs_filter: Q | None = None):
    def forwards_func(apps: Apps, schema_editor):
        # Get the model class from the apps registry.
        model_class: t.Type[Model] = apps.get_model(
            app_label="user", model_name=model_name
        )
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
        print(
            f"Updated {update_count} instances of {model_name} for field "
            f"{field_name} where {plain_field_name} is null or empty."
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
            print(
                f"No instances of {model_name} found for field {field_name} "
                f"where {plain_field_name} is not null or empty."
            )
            return
        print(
            f"Hashing {count} instances of {model_name} for field "
            f"{field_name}..."
        )

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
            print(f"({i}/{count})")

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

    return migrations.RunPython(forwards_func)


def set_user_field(field_name: str):
    return set_field(
        model_name="user", field_name=field_name, qs_filter=Q(is_active=True)
    )


def set_class_field(field_name: str):
    return set_field(
        model_name="class",
        field_name=field_name,
        qs_filter=(
            Q(is_active=True)
            & Q(teacher__isnull=False)
            & Q(teacher__school__isnull=False)
            & Q(teacher__school__is_active=True)
        ),
    )


def set_school_teacher_invitation_field(field_name: str):
    return set_field(
        model_name="schoolteacherinvitation",
        field_name=field_name,
        qs_filter=(
            Q(is_active=True)
            & Q(school__isnull=False)
            & Q(school__is_active=True)
        ),
    )


def set_school_field(field_name: str):
    return set_field(
        model_name="school", field_name=field_name, qs_filter=Q(is_active=True)
    )


user_migrations = [
    # Email
    set_user_field(field_name="email"),
    migrations.AlterField(
        model_name="user",
        name="_email_enc",
        field=EncryptedTextField(
            associated_data="email",
            db_column="email_enc",
            default=b"",
            verbose_name="email address",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="user",
        name="_email_hash",
        field=Sha256Field(
            db_column="email_hash",
            default="",
            editable=False,
            max_length=64,
            verbose_name="email hash",
        ),
        preserve_default=False,
    ),
    # First name
    set_user_field(field_name="first_name"),
    migrations.AlterField(
        model_name="user",
        name="_first_name_enc",
        field=EncryptedTextField(
            associated_data="first_name",
            db_column="first_name_enc",
            default=b"",
            verbose_name="first name",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="user",
        name="_first_name_hash",
        field=Sha256Field(
            db_column="first_name_hash",
            default="",
            editable=False,
            max_length=64,
            verbose_name="first name hash",
        ),
        preserve_default=False,
    ),
    # Last name
    set_user_field(field_name="last_name"),
    migrations.AlterField(
        model_name="user",
        name="_last_name_enc",
        field=EncryptedTextField(
            associated_data="last_name",
            db_column="last_name_enc",
            default=b"",
            verbose_name="last name",
        ),
        preserve_default=False,
    ),
    # Username
    set_user_field(field_name="username"),
    migrations.AlterField(
        model_name="user",
        name="_username_enc",
        field=EncryptedTextField(
            associated_data="username",
            db_column="username_enc",
            default=b"",
            verbose_name="username",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="user",
        name="_username_hash",
        field=Sha256Field(
            db_column="username_hash",
            default="",
            editable=False,
            max_length=64,
            unique=True,
            verbose_name="username hash",
        ),
        preserve_default=False,
    ),
]

class_migrations = [
    # Access code
    set_class_field(field_name="access_code"),
    migrations.AlterField(
        model_name="class",
        name="_access_code_enc",
        field=EncryptedTextField(
            associated_data="access_code",
            db_column="access_code_enc",
            default=b"",
            verbose_name="access code",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="class",
        name="_access_code_hash",
        field=Sha256Field(
            db_column="access_code_hash",
            default="",
            editable=False,
            max_length=64,
            verbose_name="access code hash",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="class",
        name="_access_code_plain",
        field=CharField(default="", max_length=5),
        preserve_default=False,
    ),
    # Name
    set_class_field(field_name="name"),
    migrations.AlterField(
        model_name="class",
        name="_name_enc",
        field=EncryptedTextField(
            associated_data="name",
            db_column="name_enc",
            default=b"",
            verbose_name="name",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="class",
        name="_name_hash",
        field=Sha256Field(
            db_column="name_hash",
            default="",
            editable=False,
            max_length=64,
            verbose_name="name hash",
        ),
        preserve_default=False,
    ),
]

school_teacher_invitation_migrations = [
    # Email
    set_school_teacher_invitation_field(field_name="invited_teacher_email"),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_email_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_email",
            db_column="invited_teacher_email_enc",
            default=b"",
            verbose_name="invited teacher email",
        ),
        preserve_default=False,
    ),
    # First name
    set_school_teacher_invitation_field(
        field_name="invited_teacher_first_name"
    ),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_first_name_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_first_name",
            db_column="invited_teacher_first_name_enc",
            default=b"",
            verbose_name="invited teacher first name",
        ),
        preserve_default=False,
    ),
    # Last name
    set_school_teacher_invitation_field(field_name="invited_teacher_last_name"),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_last_name_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_last_name",
            db_column="invited_teacher_last_name_enc",
            default=b"",
            verbose_name="invited teacher last name",
        ),
        preserve_default=False,
    ),
    # Token
    set_school_teacher_invitation_field(field_name="token"),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_token_enc",
        field=EncryptedTextField(
            associated_data="token",
            db_column="token_enc",
            default=b"",
            verbose_name="token",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_token_hash",
        field=Sha256Field(
            db_column="token_hash",
            default="",
            editable=False,
            max_length=64,
            unique=True,
            verbose_name="token hash",
        ),
        preserve_default=False,
    ),
]

school_migrations = [
    # Name
    set_school_field(field_name="name"),
    migrations.AlterField(
        model_name="school",
        name="_name_enc",
        field=EncryptedTextField(
            associated_data="name",
            db_column="name_enc",
            default=b"",
            verbose_name="name",
        ),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name="school",
        name="_name_hash",
        field=Sha256Field(
            db_column="name_hash",
            default="",
            editable=False,
            max_length=64,
            unique=True,
            verbose_name="name hash",
        ),
        preserve_default=False,
    ),
]


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_client_side_encryption_part_2"),
    ]

    operations = [
        *user_migrations,
        *class_migrations,
        *school_teacher_invitation_migrations,
        *school_migrations,
    ]
