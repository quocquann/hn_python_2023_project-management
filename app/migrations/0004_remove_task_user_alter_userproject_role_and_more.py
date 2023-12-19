# Generated by Django 4.2.7 on 2023-12-19 06:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("app", "0003_merge_20231208_1104"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="user",
        ),
        migrations.AlterField(
            model_name="userproject",
            name="role",
            field=models.IntegerField(
                choices=[(0, "Stage Owner"), (1, "Member"), (2, "Project Manager")],
                default=1,
                verbose_name="Role",
            ),
        ),
        migrations.DeleteModel(
            name="UserTask",
        ),
        migrations.AddField(
            model_name="task",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
