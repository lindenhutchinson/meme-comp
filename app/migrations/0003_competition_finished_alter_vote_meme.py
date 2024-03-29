# Generated by Django 4.2.1 on 2023-05-13 01:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("app", "0002_competition_current_meme_seenmeme")]

    operations = [
        migrations.AddField(
            model_name="competition",
            name="finished",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="vote",
            name="meme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votes",
                to="app.meme",
            ),
        ),
    ]
