from celery import shared_task

from .models import Meme  # Replace with the actual import path
from .utils import get_top_memes, send_channel_message, set_next_meme_for_competition # Replace with the actual import path





@shared_task
def do_advance_competition(competition):
    competition.participants.update(ready=False)
    # attempt to get a random next meme for the competition
    competition = set_next_meme_for_competition(competition.id)
    if competition.current_meme:
        # if we were able to set a random meme, update the channel to show it on the page
        data = {
            "id": competition.current_meme.id,
            "num_memes": competition.num_memes,
            "ctr": competition.meme_ctr,
        }
        send_channel_message(competition.name, "next_meme", data)
    else:
        statistics = {
            "fastest_voter": f'{competition.lowest_avg_vote_time["participant"]} averaged {competition.lowest_avg_vote_time["vote_time"]} seconds per vote',
            "slowest_voter": f'{competition.highest_avg_vote_time["participant"]} averaged {competition.highest_avg_vote_time["vote_time"]} seconds per vote',
            "highest_score_given": f'{competition.highest_avg_score_given["participant"]} gave a {competition.highest_avg_score_given["score"]} average score',
            "lowest_score_given": f'{competition.lowest_avg_score_given["participant"]} gave a {competition.lowest_avg_score_given["score"]} average score',
            "most_submitted": f'{competition.highest_memes_submitted["participant"]} submitted {competition.highest_memes_submitted["num_memes"]} memes',
            "highest_avg_score": f'{competition.highest_avg_score_received["participant"]} received a {competition.highest_avg_score_received["score"]} weighted score',
            "avg_own_score": f'{competition.lowest_avg_own_memes["participant"]} gave themselves a {competition.lowest_avg_own_memes["score"]} average score',
            "avg_meme_score": competition.avg_meme_score,
            "avg_vote_time": competition.avg_vote_time,
            "avg_vote_on_own_memes": competition.avg_vote_on_own_memes,
        }
        top_memes = get_top_memes(competition.name)
        if len(top_memes) == 1:
            top_meme = Meme.objects.get(id=top_memes[0]["id"])
            competition.winning_meme = top_meme
            competition.finished = True
            competition.tiebreaker = False

            competition.save()
            results = {
                "participant": top_meme.participant.name,
                "score": top_meme.avg_score,
                "id": top_meme.id,
                "statistics": statistics,
            }
            send_channel_message(competition.name, "competition_results", results)

        else:
            competition.tiebreaker = True
            competition.save()
            send_channel_message(competition.name, "do_tiebreaker", top_memes)
