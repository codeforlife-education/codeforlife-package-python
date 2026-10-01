import typing as t

from django.db import migrations
from django.db.migrations.state import StateApps
from django.db.models import CheckConstraint, Model, Q


def set_hash_fields_to_empty(apps: StateApps, _):
    """
    Set hash fields to empty for inactive users, classes, schools, and school
    teacher invitations.
    """

    User: t.Type[Model] = apps.get_model("user", "User")
    Class: t.Type[Model] = apps.get_model("user", "Class")
    School: t.Type[Model] = apps.get_model("user", "School")
    SchoolTeacherInvitation: t.Type[Model] = apps.get_model(
        "user", "SchoolTeacherInvitation"
    )

    is_not_active = Q(is_active=False)

    User.objects.filter(is_not_active).update(
        _username_hash="", _email_hash="", _first_name_hash=""
    )

    Class.objects.filter(is_not_active).update(
        _name_enc=b"", _name_hash="", _access_code_enc=b"", _access_code_hash=""
    )

    School.objects.filter(is_not_active).update(_name_hash="")

    SchoolTeacherInvitation.objects.filter(is_not_active).update(
        _invited_teacher_first_name_enc=b"",
        _invited_teacher_last_name_enc=b"",
        _invited_teacher_email_enc=b"",
        _token_hash="",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("user", "0006_client_side_encryption_part_4"),
    ]

    operations = [
        migrations.RunPython(set_hash_fields_to_empty),
        migrations.AddConstraint(
            model_name="class",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True), ("_name_enc", b""), _connector="OR"
                ),
                name="klass__name_enc_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="class",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True), ("_name_hash", ""), _connector="OR"
                ),
                name="klass__name_hash_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="class",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True),
                    ("_access_code_enc", b""),
                    _connector="OR",
                ),
                name="klass__access_code_enc_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="class",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True),
                    ("_access_code_hash", ""),
                    _connector="OR",
                ),
                name="klass__access_code_hash_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="school",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True), ("_name_hash", ""), _connector="OR"
                ),
                name="school__name_hash_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="schoolteacherinvitation",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True),
                    ("_invited_teacher_first_name_enc", b""),
                    _connector="OR",
                ),
                name="school_teacher_invitation__invited_teacher_first_name_enc_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="schoolteacherinvitation",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True),
                    ("_invited_teacher_last_name_enc", b""),
                    _connector="OR",
                ),
                name="school_teacher_invitation__invited_teacher_last_name_enc_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="schoolteacherinvitation",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True),
                    ("_invited_teacher_email_enc", b""),
                    _connector="OR",
                ),
                name="school_teacher_invitation__invited_teacher_email_enc_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="schoolteacherinvitation",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True), ("_token_hash", ""), _connector="OR"
                ),
                name="school_teacher_invitation__token_hash_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True), ("_email_hash", ""), _connector="OR"
                ),
                name="user__email_hash_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True), ("_username_hash", ""), _connector="OR"
                ),
                name="user__username_hash_non_empty_when_inactive",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=CheckConstraint(
                condition=Q(
                    ("is_active", True),
                    ("_first_name_hash", ""),
                    _connector="OR",
                ),
                name="user__first_name_hash_non_empty_when_inactive",
            ),
        ),
    ]
