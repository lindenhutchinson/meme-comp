


from django.urls import reverse
from django.template.loader import render_to_string
from app.utils import send_channel_message


def send_next_meme(competition):
    competition.refresh_from_db()
    meme_url = reverse('serve_file', kwargs={'comp_name':competition.name, 'meme_id':competition.current_meme.id})
    data = {
        "url": meme_url,
        "num_memes": competition.num_memes,
        "ctr": competition.meme_ctr,
    }

    send_channel_message(competition.name, "nextMeme", data)

def send_meme_uploaded(competition):
    competition.refresh_from_db()

    send_channel_message(
        competition.name,
        "memeUploaded",
        {
            "num_memes": competition.num_memes, 
            "num_uploaders": competition.num_uploaders
        },
    )

def send_participant_joined(competition, participant):
    participant_html = render_to_string("ws_tags/participant_li.html", {'participant':participant})
    data = {
        "num_participants": competition.participants.count(),
        "name": participant.name,
        "participant_html":participant_html
    }
    send_channel_message(competition.name, "participantJoined", data)

def send_competition_finished(competition):
    winner_html = render_to_string("ws_tags/winning_meme_div", {'competition':competition})
    results_html = render_to_string("ws_tags/comp_results_div", {'competition':competition})
    data = {
        "winner_html":winner_html,
        "results_html":results_html
    }
    send_channel_message(competition.name, "competitionFinished", data)