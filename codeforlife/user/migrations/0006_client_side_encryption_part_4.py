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
        name="_username_enc",
        field=EncryptedTextField(
            associated_data="username",
            verbose_name="username",
            db_column="username_enc",
        ),
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
    migrations.AlterField(
        model_name="user",
        name="_first_name_enc",
        field=EncryptedTextField(
            associated_data="first_name",
            verbose_name="first name",
            db_column="first_name_enc",
        ),
    ),
    migrations.AlterField(
        model_name="user",
        name="_first_name_hash",
        field=Sha256Field(
            editable=False,
            max_length=64,
            verbose_name="first name hash",
            db_column="first_name_hash",
        ),
    ),
    # Last name
    migrations.RemoveField(
        model_name="user",
        name="_last_name_plain",
    ),
    migrations.AlterField(
        model_name="user",
        name="_last_name_enc",
        field=EncryptedTextField(
            associated_data="last_name",
            verbose_name="last name",
            db_column="last_name_enc",
        ),
    ),
    # Email
    migrations.RemoveField(
        model_name="user",
        name="_email_plain",
    ),
    migrations.AlterField(
        model_name="user",
        name="_email_enc",
        field=EncryptedTextField(
            associated_data="email",
            verbose_name="email address",
            db_column="email_enc",
        ),
    ),
    migrations.AlterField(
        model_name="user",
        name="_email_hash",
        field=Sha256Field(
            editable=False,
            max_length=64,
            verbose_name="email hash",
            db_column="email_hash",
        ),
    ),
]

class_migrations = [
    # Name
    migrations.RemoveField(
        model_name="class",
        name="_name_plain",
    ),
    migrations.AlterField(
        model_name="class",
        name="_name_enc",
        field=EncryptedTextField(
            associated_data="name",
            verbose_name="name",
            db_column="name_enc",
        ),
    ),
    migrations.AlterField(
        model_name="class",
        name="_name_hash",
        field=Sha256Field(
            editable=False,
            max_length=64,
            verbose_name="name hash",
            db_column="name_hash",
        ),
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
        name="_token_enc",
        field=EncryptedTextField(
            associated_data="token",
            verbose_name="token",
            db_column="token_enc",
        ),
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
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_first_name_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_first_name",
            verbose_name="invited teacher first name",
            db_column="invited_teacher_first_name_enc",
        ),
    ),
    # Last name
    migrations.RemoveField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_last_name_plain",
    ),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_last_name_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_last_name",
            verbose_name="invited teacher last name",
            db_column="invited_teacher_last_name_enc",
        ),
    ),
    # Email
    migrations.RemoveField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_email_plain",
    ),
    migrations.AlterField(
        model_name="schoolteacherinvitation",
        name="_invited_teacher_email_enc",
        field=EncryptedTextField(
            associated_data="invited_teacher_email",
            verbose_name="invited teacher email",
            db_column="invited_teacher_email_enc",
        ),
    ),
]

school_migrations = [
    # Name
    migrations.RemoveField(
        model_name="school",
        name="_name_plain",
    ),
    migrations.AlterField(
        model_name="school",
        name="_name_enc",
        field=EncryptedTextField(
            associated_data="name",
            verbose_name="name",
            db_column="name_enc",
        ),
    ),
    migrations.AlterField(
        model_name="school",
        name="_name_hash",
        field=Sha256Field(
            editable=False,
            max_length=64,
            verbose_name="name hash",
            db_column="name_hash",
        ),
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
