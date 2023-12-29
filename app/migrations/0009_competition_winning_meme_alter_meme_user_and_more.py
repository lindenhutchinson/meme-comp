# Generated by Django 4.2.1 on 2023-07-21 14:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Sum, Count, F


def populate_winning_meme(apps, schema_editor):
    Competition = apps.get_model("app", "Competition")

    for competition in Competition.objects.all():
        # Get the top meme for the competition
        top_meme = (
            competition.memes.annotate(
                vote_count=Count("votes"), total=Sum("votes__score")
            )
            .annotate(vote_score=F("total") / Count("votes", distinct=True))
            .order_by("-vote_score")
            .first()
        )
        if top_meme:
            # Set the top meme as the winning meme for the competition
            competition.winning_meme = top_meme
            competition.save()


class Migration(migrations.Migration):

    dependencies = [("app", "0008_meme_user_vote_user_alter_vote_participant")]

    operations = [
        migrations.AlterField(
            model_name="meme",
            name="user",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="memes",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="participant",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="participants",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="vote",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="competition",
            name="winning_meme",
            field=models.ForeignKey(
                null=True,
                on_delete=models.SET_NULL,
                to="app.meme",
                related_name="won_competition",
            ),
        ),
        migrations.RunPython(populate_winning_meme),
    ]
