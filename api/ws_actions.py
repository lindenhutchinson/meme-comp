from django.urls import reverse_lazy
from django.template.loader import render_to_string
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from app.models.competition_log import CompetitionLog

def create_competition_log(competition, user, event):
    comp_log = CompetitionLog.objects.create(
        competition=competition, user=user, event=event
    )
    comp_log.save()
    
    # updating of events has been disabled for now
    # unnecessary use of resources, might add it back if/when live chat gets added
    # log_html = render_to_string(
    #     "ws_tags/event_log_div.html", {"event": comp_log}
    # )
    # send_channel_message(
    #     competition.name,
    #     "eventUpdated",
    #     {"log_html": log_html},
    # )


# todo - add signals to model changes and use this
def send_channel_message(comp_name, command, data=None):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        comp_name, {"type": "send_update", "data": data, "command": command}
    )

def send_next_meme(competition):
    competition.refresh_from_db()
    meme_url = reverse_lazy(
        "serve_file",
        kwargs={"comp_name": competition.name, "meme_id": competition.current_meme.id},
    )

    send_channel_message(
        competition.name,
        "nextMeme",
        {
            "url": str(meme_url),
            "num_memes": competition.num_memes,
            "ctr": competition.meme_ctr,
        },
    )
    create_competition_log(
        competition, competition.owner, CompetitionLog.CompActions.ADVANCE
    )

    # whenever the next meme is started, we need to start the voting timer



def send_meme_uploaded(competition):
    competition.refresh_from_db()

    send_channel_message(
        competition.name,
        "memeUploaded",
        {
            "num_memes": competition.num_memes,
            "num_uploaders": competition.num_uploaders,
        },
    )


def send_participant_joined(competition, participant):
    participant_html = render_to_string(
        "ws_tags/participant_li.html", {"participant": participant}
    )

    send_channel_message(
        competition.name,
        "participantJoined",
        data={
            "num_participants": competition.participants.count(),
            "name": participant.name,
            "participant_html": participant_html,
        },
    )
    create_competition_log(
        competition, participant.user, CompetitionLog.CompActions.JOIN
    )


def send_competition_finished(competition):
    winner_html = render_to_string(
        "ws_tags/winning_meme_div.html", {"winning_meme": competition.winning_meme}
    )
    results_html = render_to_string(
        "ws_tags/comp_results_div.html", {"competition": competition}
    )
    send_channel_message(
        competition.name,
        "competitionFinished",
        {"winner_html": winner_html, "results_html": results_html},
    )
    create_competition_log(
        competition, competition.winning_meme.user, CompetitionLog.CompActions.WON
    )
