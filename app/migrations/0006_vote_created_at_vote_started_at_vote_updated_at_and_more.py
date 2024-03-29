# Generated by Django 4.2.1 on 2023-05-20 13:45

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [("app", "0005_participant_active_alter_vote_score")]

    operations = [
        migrations.AddField(
            model_name="vote",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="vote",
            name="started_at",
            field=models.DateTimeField(default=None),
        ),
        migrations.AddField(
            model_name="vote",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="participant",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]
