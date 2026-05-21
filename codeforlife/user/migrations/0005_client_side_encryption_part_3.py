from django.db import migrations
from django.db.models import CharField, Q, UniqueConstraint

from ...models.fields import EncryptedTextField, Sha256Field

user_migrations = [
    # Email
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
            verbose_name="username hash",
        ),
        preserve_default=False,
    ),
    migrations.AddConstraint(
        model_name="user",
        constraint=UniqueConstraint(
            condition=Q(("_username_hash", ""), _negated=True),
            fields=("_username_hash",),
            name="unique_username_hash_non_empty",
        ),
    ),
]

class_migrations = [
    # Access code
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
    migrations.AddConstraint(
        model_name="class",
        constraint=UniqueConstraint(
            condition=Q(("_access_code_hash", ""), _negated=True),
            fields=("_access_code_hash",),
            name="unique_access_code_hash_non_empty",
        ),
    ),
    migrations.AlterField(
        model_name="class",
        name="_access_code_plain",
        field=CharField(default="", max_length=5),
        preserve_default=False,
    ),
    # Name
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
            verbose_name="token hash",
        ),
        preserve_default=False,
    ),
    migrations.AddConstraint(
        model_name="schoolteacherinvitation",
        constraint=UniqueConstraint(
            condition=Q(("_token_hash", ""), _negated=True),
            fields=("_token_hash",),
            name="unique_token_hash_non_empty",
        ),
    ),
]

school_migrations = [
    # Name
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
