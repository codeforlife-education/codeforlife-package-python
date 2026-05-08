from django.db import migrations

from ...models.fields import (
    DataEncryptionKeyField,
    EncryptedTextField,
    Sha256Field,
)
from ..models.user import UserManager

user_migrations = [
    migrations.AlterModelManagers(
        name="user",
        managers=[("objects", UserManager())],
    ),
    migrations.AddField(
        model_name="user",
        name="dek",
        field=DataEncryptionKeyField(
            editable=False,
            help_text="The encrypted data encryption key (DEK) for this model.",
            null=True,
            verbose_name="data encryption key",
        ),
    ),
    # Username
    migrations.RenameField(
        model_name="user",
        old_name="username",
        new_name="_username_plain",
    ),
    migrations.AddField(
        model_name="user",
        name="_username_enc",
        field=EncryptedTextField(
            associated_data="username",
            null=True,
            verbose_name="username",
            db_column="username_enc",
        ),
    ),
    migrations.AddField(
        model_name="user",
        name="_username_hash",
        field=Sha256Field(
            null=True,
            unique=True,
            editable=False,
            max_length=64,
            verbose_name="username hash",
            db_column="username_hash",
        ),
    ),
    # Email
    migrations.RenameField(
        model_name="user",
        old_name="email",
        new_name="_email_plain",
    ),
    migrations.AddField(
        model_name="user",
        name="_email_enc",
        field=EncryptedTextField(
            associated_data="email",
            null=True,
            verbose_name="email address",
            db_column="email_enc",
        ),
    ),
    migrations.AddField(
        model_name="user",
        name="_email_hash",
        field=Sha256Field(
            null=True,
            editable=False,
            max_length=64,
            verbose_name="email hash",
            db_column="email_hash",
        ),
    ),
    # First name
    migrations.RenameField(
        model_name="user",
        old_name="first_name",
        new_name="_first_name_plain",
    ),
    migrations.AddField(
        model_name="user",
        name="_first_name_enc",
        field=EncryptedTextField(
            associated_data="first_name",
            null=True,
            verbose_name="first name",
            db_column="first_name_enc",
        ),
    ),
    migrations.AddField(
        model_name="user",
        name="_first_name_hash",
        field=Sha256Field(
            null=True,
            editable=False,
            max_length=64,
            verbose_name="first name hash",
            db_column="first_name_hash",
        ),
    ),
    # Last name
    migrations.RenameField(
        model_name="user",
        old_name="last_name",
        new_name="_last_name_plain",
    ),
    migrations.AddField(
        model_name="user",
        name="_last_name_enc",
        field=EncryptedTextField(
            associated_data="last_name",
            null=True,
            verbose_name="last name",
            db_column="last_name_enc",
        ),
    ),
]

class_migrations = [
    # Access code
    migrations.RenameField(
        model_name="class",
        old_name="access_code",
        new_name="_access_code_plain",
    ),
    migrations.AddField(
        model_name="class",
        name="_access_code_enc",
        field=EncryptedTextField(
            associated_data="access_code",
            null=True,
            verbose_name="access code",
            db_column="access_code_enc",
        ),
    ),
    migrations.AddField(
        model_name="class",
        name="_access_code_hash",
        field=Sha256Field(
            null=True,
            editable=False,
            max_length=64,
            verbose_name="access code hash",
            db_column="access_code_hash",
        ),
    ),
    # Name
    migrations.RenameField(
        model_name="class",
        old_name="name",
        new_name="_name_plain",
    ),
    migrations.AddField(
        model_name="class",
        name="_name_enc",
        field=EncryptedTextField(
            associated_data="name",
            null=True,
            verbose_name="name",
            db_column="name_enc",
        ),
    ),
]

school_teacher_invitation_migrations = [
    # Token
    migrations.RenameField(
        model_name="schoolteacherinvitation",
        old_name="token",
        new_name="_token_plain",
    ),
    migrations.AddField(
        model_name="schoolteacherinvitation",
        name="_token_enc",
        field=EncryptedTextField(
            associated_data="token",
            null=True,
            verbose_name="token",
            db_column="token_enc",
        ),
    ),
    migrations.AddField(
        model_name="schoolteacherinvitation",
        name="_token_hash",
        field=Sha256Field(
            null=True,
            editable=False,
            max_length=64,
            verbose_name="token hash",
            db_column="token_hash",
        ),
    ),
    # Invited teacher first name
    migrations.RenameField(
        model_name="schoolteacherinvitation",
        old_name="invited_teacher_first_name",
        new_name="_invited_teacher_first_name_plain",
    ),
    migrations.AddField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_first_name_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_first_name",
            null=True,
            verbose_name="invited teacher first name",
            db_column="invited_teacher_first_name_enc",
        ),
    ),
    # Invited teacher last name
    migrations.RenameField(
        model_name="schoolteacherinvitation",
        old_name="invited_teacher_last_name",
        new_name="_invited_teacher_last_name_plain",
    ),
    migrations.AddField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_last_name_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_last_name",
            null=True,
            verbose_name="invited teacher last name",
            db_column="invited_teacher_last_name_enc",
        ),
    ),
    # Invited teacher email
    migrations.RenameField(
        model_name="schoolteacherinvitation",
        old_name="invited_teacher_email",
        new_name="_invited_teacher_email_plain",
    ),
    migrations.AddField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_email_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_email",
            null=True,
            verbose_name="invited teacher email",
            db_column="invited_teacher_email_enc",
        ),
    ),
]

school_migrations = [
    migrations.AddField(
        model_name="school",
        name="dek",
        field=DataEncryptionKeyField(
            editable=False,
            help_text="The encrypted data encryption key (DEK) for this model.",
            null=True,
            verbose_name="data encryption key",
        ),
    ),
    # Name
    migrations.RenameField(
        model_name="school",
        old_name="name",
        new_name="_name_plain",
    ),
    migrations.AddField(
        model_name="school",
        name="_name_enc",
        field=EncryptedTextField(
            associated_data="name",
            null=True,
            verbose_name="name",
            db_column="name_enc",
        ),
    ),
]


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0002_user_proxies_and_new_models"),
    ]

    operations = [
        *user_migrations,
        *class_migrations,
        *school_teacher_invitation_migrations,
        *school_migrations,
    ]
