# Generated by Django 4.2.1 on 2023-10-06 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0012_alter_competition_current_meme_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="ready",
            field=models.BooleanField(default=False),
        ),
    ]