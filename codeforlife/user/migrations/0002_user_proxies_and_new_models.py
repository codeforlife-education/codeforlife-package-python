import codeforlife.models.fields.encrypted_text
import codeforlife.user.models.user.admin_school_teacher
import codeforlife.user.models.user.contactable
import codeforlife.user.models.user.google
import codeforlife.user.models.user.independent
import codeforlife.user.models.user.non_admin_school_teacher
import codeforlife.user.models.user.non_school_teacher
import codeforlife.user.models.user.school_teacher
import codeforlife.user.models.user.student
import codeforlife.user.models.user.teacher
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactableUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.user",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.contactable.ContactableUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StudentUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.user",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.student.StudentUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AuthFactor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.TextField(choices=[("otp", "one-time password")]),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="auth_factors",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "type")},
            },
        ),
        migrations.CreateModel(
            name="OtpBypassToken",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "token",
                    codeforlife.models.fields.encrypted_text.EncryptedTextField(
                        associated_data="token",
                        help_text="The encrypted equivalent of the token.",
                        verbose_name="token",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otp_bypass_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "OTP bypass token",
                "verbose_name_plural": "OTP bypass tokens",
            },
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "session_key",
                    models.CharField(
                        max_length=40,
                        primary_key=True,
                        serialize=False,
                        verbose_name="session key",
                    ),
                ),
                ("session_data", models.TextField(verbose_name="session data")),
                (
                    "expire_date",
                    models.DateTimeField(
                        db_index=True, verbose_name="expire date"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "session",
                "verbose_name_plural": "sessions",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Independent",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.student",),
        ),
        migrations.CreateModel(
            name="NonSchoolTeacher",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.teacher",),
        ),
        migrations.CreateModel(
            name="SchoolTeacher",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.teacher",),
        ),
        migrations.CreateModel(
            name="GoogleUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.contactableuser",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.google.GoogleUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IndependentUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.contactableuser",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.independent.IndependentUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TeacherUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.contactableuser",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.teacher.TeacherUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SessionAuthFactor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "auth_factor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="user.authfactor",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="auth_factors",
                        to="user.session",
                    ),
                ),
            ],
            options={
                "unique_together": {("session", "auth_factor")},
            },
        ),
        migrations.CreateModel(
            name="AdminSchoolTeacher",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.schoolteacher",),
        ),
        migrations.CreateModel(
            name="NonAdminSchoolTeacher",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.schoolteacher",),
        ),
        migrations.CreateModel(
            name="NonSchoolTeacherUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.teacheruser",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.non_school_teacher.NonSchoolTeacherUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SchoolTeacherUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.teacheruser",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.school_teacher.SchoolTeacherUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AdminSchoolTeacherUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.schoolteacheruser",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.admin_school_teacher.AdminSchoolTeacherUserManager(),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NonAdminSchoolTeacherUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("user.schoolteacheruser",),
            managers=[
                (
                    "objects",
                    codeforlife.user.models.user.non_admin_school_teacher.NonAdminSchoolTeacherUserManager(),
                ),
            ],
        ),
    ]
