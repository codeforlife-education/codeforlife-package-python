import typing as t

from django.apps.registry import Apps
from django.db import migrations
from django.db.models import CharField, Model, Q

from ...models.fields import EncryptedTextField, Sha256Field


def set_field(model_name: str, field_name: str, qs_filter: Q | None = None):
    def forwards_func(apps: Apps, schema_editor):
        # Get the model class from the apps registry.
        model_class: t.Type[Model] = apps.get_model(
            app_label="user", model_name=model_name
        )

        # Helper function to create a Q object that checks if a field is null or
        # empty.
        def null_or_empty(field_name: str, empty: t.Any):
            return Q(**{f"{field_name}__isnull": True}) | Q(
                **{f"{field_name}": empty}
            )

        # Define the names and default values for the plain, encrypted, and hash
        # fields.
        plain_field = f"_{field_name}_plain", ""
        enc_field = f"_{field_name}_enc", b""
        hash_field = f"_{field_name}_hash", ""

        # Check if the encrypted and hash fields exist.
        has_enc_field = enc_field[0] in model_class._meta.fields_map
        has_hash_field = hash_field[0] in model_class._meta.fields_map

        # Build the queryset to filter instances where the plain field is not
        # null or empty, and either the encrypted field or hash field is null or
        # empty (if they exist).
        queryset = model_class.objects.filter(  # type: ignore[attr-defined]
            ~null_or_empty(*plain_field)
            & (
                null_or_empty(*enc_field) | null_or_empty(*hash_field)
                if has_enc_field and has_hash_field
                else (
                    null_or_empty(*enc_field)
                    if has_enc_field
                    else null_or_empty(*hash_field)
                )
            )
        )

        # Additional filter if provided.
        if qs_filter is not None:
            queryset = queryset.filter(qs_filter)

        # Select fields.
        fields = [plain_field[0]]
        if has_enc_field:
            fields.append(enc_field[0])
        if has_hash_field:
            fields.append(hash_field[0])
        queryset = queryset.only(*fields)

        # Iterate over the queryset in chunks and save each instance.
        for instance in queryset.iterator(chunk_size=1000):
            # Get the plain value.
            value = getattr(instance, plain_field[0])

            # Set the plain, encrypted and hash values.
            setattr(instance, field_name, value)

            # Save the instance, updating only the relevant fields.
            instance.save(update_fields=fields)

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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
            default="",
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
