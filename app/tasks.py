from datetime import datetime
import random
from celery import shared_task
from django.urls import reverse

from api.ws_actions import send_competition_finished
from .models import Meme, Competition
from .utils import (
    get_top_memes,
    send_channel_message,
    set_next_meme_for_competition,
    redis_lock,
)
from django.template.loader import render_to_string


# @shared_task(ignore_result=True)
def do_advance_competition(competition_id):
    competition = Competition.objects.get(id=competition_id)

    competition.participants.update(ready=False)
    # attempt to get a random next meme for the competition
    competition = set_next_meme_for_competition(competition.id)

    if competition.current_meme:
        # if we were able to set a random meme, update the channel to show it on the page
        data = {
            "url": reverse('serve_file', kwargs={'comp_name':competition.name, 'meme_id':competition.current_meme.id}),
            "num_memes": competition.num_memes,
            "ctr": competition.meme_ctr,
        }
        send_channel_message(competition.name, "nextMeme", data)
    else:
        top_memes = get_top_memes(competition.name)
        if len(top_memes) == 1:
            top_meme = Meme.objects.get(id=top_memes[0]["id"])
        else:
            top_meme = random.choice(top_memes)
            
        competition.winning_meme = top_meme
        competition.finished = True
        send_competition_finished(competition)

    # competition has been advanced, toggle the timer inactive
    competition.timer_active = False
    competition.save()
