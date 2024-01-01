# Generated by Django 4.2.1 on 2024-01-01 02:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("app", "0020_alter_competition_timer_timeout")]

    operations = [
        migrations.RemoveField(model_name="competition", name="finished"),
        migrations.RemoveField(model_name="competition", name="started"),
        migrations.RemoveField(model_name="competition", name="tiebreaker"),
        migrations.AddField(
            model_name="competition",
            name="state",
            field=models.CharField(
                choices=[
                    ("unstarted", "Unstarted"),
                    ("started", "Started"),
                    ("tiebreak", "Tiebreak"),
                    ("finished", "Finished"),
                ],
                default="unstarted",
                max_length=10,
            ),
        ),
    ]
