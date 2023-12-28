from django.urls import reverse_lazy
from django.template.loader import render_to_string
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
