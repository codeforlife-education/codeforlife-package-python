from django.db import migrations

from ...models.fields import EncryptedTextField, Sha256Field

user_migrations = [
    # Username
    migrations.RemoveField(
        model_name="user",
        name="_username_plain",
    ),
    migrations.AlterField(
        model_name="user",
        name="_username_hash",
        field=Sha256Field(
            unique=True,
            editable=False,
            max_length=64,
            verbose_name="username hash",
            db_column="username_hash",
        ),
    ),
    # First name
    migrations.RemoveField(
        model_name="user",
        name="_first_name_plain",
    ),
    # Last name
    migrations.RemoveField(
        model_name="user",
        name="_last_name_plain",
    ),
    # Email
    migrations.RemoveField(
        model_name="user",
        name="_email_plain",
    ),
]

class_migrations = [
    # Name
    migrations.RemoveField(
        model_name="class",
        name="_name_plain",
    ),
    # Access code
    migrations.RemoveField(
        model_name="class",
        name="_access_code_plain",
    ),
]

school_teacher_invitation_migrations = [
    # Token
    migrations.RemoveField(
        model_name="schoolteacherinvitation",
        name="_token_plain",
    ),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_token_hash",
        field=Sha256Field(
            unique=True,
            editable=False,
            max_length=64,
            verbose_name="token hash",
            db_column="token_hash",
        ),
    ),
    # First name
    migrations.RemoveField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_first_name_plain",
    ),
    # Last name
    migrations.RemoveField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_last_name_plain",
    ),
    # Email
    migrations.RemoveField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_email_plain",
    ),
]

school_migrations = [
    # Name
    migrations.RemoveField(
        model_name="school",
        name="_name_plain",
    ),
]


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0005_client_side_encryption_part_3"),
    ]

    operations = [
        *user_migrations,
        *class_migrations,
        *school_teacher_invitation_migrations,
        *school_migrations,
    ]
