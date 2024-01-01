import re
from django.contrib.auth import get_user_model
import random
import string

from api.ws_actions import (
    send_competition_finished,
    send_next_meme,
    send_channel_message,
)
from .models import Competition, SeenMeme, Meme, CompetitionLog

from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from datetime import datetime
from MemeComp.celery import app

def redirect_and_flash_error(request, error):
    messages.error(request, error)
    return redirect("home")


def generate_random_string(length):
    """Generate a random string up to the given maximum length."""
    valid_chars = [
        c for c in string.ascii_letters if c not in ["l", "I", "i", "O", "o"]
    ]
    return "".join(random.choice(valid_chars) for _ in range(length))


def get_current_user(request):
    user_id = request.session.get("user_id")
    if user_id:
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            pass
    return None


def send_shame_message(comp_name, username):
    messages = [
        f"{username} thinks they're a hackerman.",
        f"{username} is trying to do something they shouldn't.",
        f"{username} is why we can't have nice things.",
        f"{username} used hack! It's not very effective...",
        f"Warning: {username} is attempting to break into the secret cookie jar.",
        f"Attention! {username} is testing their hacking skills.",
        f"Caution: {username} is attempting to hack their way to world domination.",
        f"Attention: {username} is currently experiencing technical difficulties in their hacking endeavours.",
        f"Error 404: {username}'s hacking skills not found. Please check your connection to the Matrix and try again.",
        f"Congratulations, {username}! You've been nominated for the 'Best Attempted Hack of the Year' award.",
        f"Warning: {username} is conducting a secret hacking mission.",
    ]
    message = random.choice(messages)
    send_channel_message(comp_name, "update_shame", message)


def check_emoji_text(text):
    try:
        emoji = re.search(r"(\d{4,6})", f"{ord(text)}")
        emoji_text = chr(int(emoji.group(1)))
        return emoji_text or False
    except TypeError:
        return False


def num_votes_for_round(competition):
    competition.refresh_from_db()
    # Get the votes updated before the competition's round_started_at timestamp
    # the competition was last updated when the current_meme was set at the start of this round.

    votes_updated_before_competition = (
        competition.votes.filter(updated_at__gt=competition.round_started_at)
        .values("user_id")
        .distinct()
    )
    return votes_updated_before_competition.count()


def get_random_object_from_query(obj_class, query):
    pks = query.values_list("pk", flat=True)
    random_pk = random.choice(pks)
    return obj_class.objects.get(pk=random_pk)


def revoke_competition_timer(competition):
    if competition.timer_task_id:
        # we need to cancel the timer task and clear the timer task id
        app.control.revoke(competition.timer_task_id)
        competition.timer_task_id = None
        competition.timer_started_at = None
        competition.save()

def run_advance_competition(competition, as_task=False):
    """
    Run the advancement of a meme competition.

    Parameters:
        competition (MemeCompetition): The competition object to advance.
        as_task (bool, optional): Indicates whether this function is running as a Celery task.
                                  If True, it won't attempt to revoke itself.

    Note:
        This function advances the competition by setting the next meme, handling competition
        completion, and sending appropriate notifications.

    Returns:
        None
    """
    # If not running as a task, revoke the competition timer
    if not as_task:
        revoke_competition_timer(competition)

    
    # Attempt to get a random next meme for the competition
    competition = set_next_meme_for_competition(competition)
    competition.refresh_from_db()

    if competition.current_meme:
        # If we were able to set the next meme, the competition hasn't finished yet
        send_next_meme(competition)
    else:
        # If no current_meme exists, the competition is finished

        if competition.top_memes.count() == 1:
            # If only one meme has the top score, it is the winner
            top_meme = competition.top_memes.first()
        else:
            # Otherwise, resolve tiebreakers randomly
            top_meme = get_random_object_from_query(Meme, competition.top_memes)
            
        competition.winning_meme = top_meme
        competition.state = Competition.CompState.FINISHED
        competition.save()
        send_competition_finished(competition)
        

def set_next_meme_for_competition(competition):
    """
    Set the next meme for the given competition.

    Parameters:
        competition (MemeCompetition): The competition object for which to set the next meme.

    Returns:
        MemeCompetition: The updated competition object.
    """
    # Get the list of all memes for the competition
    all_memes = competition.memes.all()

    # Get the list of seen memes for the competition
    seen_memes = SeenMeme.objects.filter(competition=competition).values_list(
        "meme", flat=True
    )

    # Exclude the seen memes from the list of all memes
    available_memes = all_memes.exclude(id__in=seen_memes)

    # Select a random meme from the available memes
    if available_memes.exists():
        random_meme = random.choice(available_memes)
        # Set the competition's current_meme to the randomly selected meme
        competition.current_meme = random_meme

        # Create a SeenMeme object for the selected meme and competition
        SeenMeme.objects.create(meme=random_meme, competition=competition)
    else:
        competition.current_meme = None

    # Update round start time and save the competition
    competition.round_started_at = datetime.now(tz=timezone.get_current_timezone())
    competition.save()
    return competition