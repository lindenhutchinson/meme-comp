# Generated by Django 4.2.1 on 2023-07-21 13:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db import migrations, models
from django.contrib.auth import get_user_model

User = get_user_model()


def set_user_for_existing_votes(apps, schema_editor):
    Vote = apps.get_model("app", "Vote")
    Participant = apps.get_model("app", "Participant")

    for vote in Vote.objects.all():
        participant = Participant.objects.filter(id=vote.participant_id).first()
        if participant:
            vote.user = participant.user
            vote.save()


def set_user_for_existing_memes(apps, schema_editor):
    Meme = apps.get_model("app", "Meme")
    Participant = apps.get_model("app", "Participant")

    for meme in Meme.objects.all():
        participant = Participant.objects.filter(id=meme.participant_id).first()
        if participant:
            meme.user = participant.user
            meme.save()


def reverse_user_for_existing_memes(apps, schema_editor):
    Meme = apps.get_model("app", "Meme")
    for meme in Meme.objects.all():
        meme.user = None  # Or choose a default user if applicable
        meme.save()


def reverse_user_for_existing_votes(apps, schema_editor):
    Vote = apps.get_model("app", "Vote")
    for vote in Vote.objects.all():
        vote.user = None  # Or choose a default user if applicable
        vote.save()


class Migration(migrations.Migration):

    dependencies = [("app", "0007_vote_competition")]

    operations = [
        migrations.AddField(
            model_name="meme",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="memes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="vote",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="vote",
            name="participant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votes",
                to="app.participant",
            ),
        ),
        migrations.RunPython(
            set_user_for_existing_memes, reverse_user_for_existing_memes
        ),
        migrations.RunPython(
            set_user_for_existing_votes, reverse_user_for_existing_votes
        ),
    ]
