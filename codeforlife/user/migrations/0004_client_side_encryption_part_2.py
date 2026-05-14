from django.db import migrations

from ...models.fields import Sha256Field


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0003_client_side_encryption_part_1"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schoolteacherinvitation",
            name="_token_hash",
            field=Sha256Field(
                null=True,
                db_column="token_hash",
                editable=False,
                max_length=64,
                unique=True,
                verbose_name="token hash",
            ),
        ),
        migrations.AddField(
            model_name="school",
            name="_name_hash",
            field=Sha256Field(
                null=True,
                unique=True,
                editable=False,
                max_length=64,
                verbose_name="name hash",
                db_column="name_hash",
            ),
        ),
        migrations.AddField(
            model_name="class",
            name="_name_hash",
            field=Sha256Field(
                null=True,
                editable=False,
                max_length=64,
                verbose_name="name hash",
                db_column="name_hash",
            ),
        ),
    ]
