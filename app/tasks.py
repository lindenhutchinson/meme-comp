from datetime import datetime
from celery import shared_task
from .models import Meme, Competition
from .utils import (
    get_top_memes,
    send_channel_message,
    set_next_meme_for_competition,
    redis_lock,
)


@shared_task(ignore_result=True)
def do_advance_competition(competition_id):
    competition = Competition.objects.get(id=competition_id)

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
        top_memes = get_top_memes(competition.name)
        if len(top_memes) == 1:
            fastest_slowest_voter = competition.get_avg_vote_time_extrema()
            highest_avg_score_given = competition.get_avg_score_given_extrema()['highest']
            lowest_avg_score_given = competition.get_avg_score_given_extrema()['lowest']
            most_submitted = competition.highest_memes_submitted()
            highest_avg_score_received = competition.highest_avg_score_received()
            lowest_avg_own_memes = competition.lowest_avg_own_memes()

            statistics = {
                "fastest_voter": f"{fastest_slowest_voter['lowest']['participant']} averaged {fastest_slowest_voter['lowest']['vote_time']} seconds per vote",
                "slowest_voter": f"{fastest_slowest_voter['highest']['participant']} averaged {fastest_slowest_voter['highest']['vote_time']} seconds per vote",
                "highest_score_given": f"{highest_avg_score_given['participant']} gave a {highest_avg_score_given['score']} average score",
                "lowest_score_given": f"{lowest_avg_score_given['participant']} gave a {lowest_avg_score_given['score']} average score",
                "most_submitted": f"{most_submitted['participant']} submitted {most_submitted['num_memes']} memes",
                "highest_avg_score": f"{highest_avg_score_received['participant']} received a {highest_avg_score_received['score']} weighted score",
                "avg_own_score": f"{lowest_avg_own_memes['participant']} gave themselves a {lowest_avg_own_memes['score']} average score",
                "avg_meme_score": competition.avg_meme_score(),
                "avg_vote_time": competition.avg_vote_time(),
                "avg_vote_on_own_memes": competition.avg_vote_on_own_memes(),
            }
            top_meme = Meme.objects.get(id=top_memes[0]["id"])
            competition.winning_meme = top_meme
            competition.finished = True
            competition.tiebreaker = False
            results = {
                "participant": top_meme.participant.name,
                "score": top_meme.avg_score,
                "id": top_meme.id,
                "statistics": statistics,
            }
            send_channel_message(competition.name, "competition_results", results)

        else:
            competition.tiebreaker = True
            send_channel_message(competition.name, "do_tiebreaker", top_memes)

    # competition has been advanced, toggle the timer inactive
    competition.timer_active = False
    competition.save()
