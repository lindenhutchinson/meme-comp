# Generated by Django 4.2.1 on 2023-05-20 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_competition_updated_at_alter_competition_created_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="active",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="vote",
            name="score",
            field=models.IntegerField(
                choices=[
                    (0, "0 - Just Awful"),
                    (1, "1 - Terrible"),
                    (2, "2 - Below Average"),
                    (3, "3 - Average"),
                    (4, "4 - Good"),
                    (5, "5 - Excellent"),
                ]
            ),
        ),
    ]