import copy
from django.db import models
from django.utils import timezone
from django.db.models import (
    Avg,
    Sum,
    Count,
    F,
    ExpressionWrapper,
    FloatField,
    StdDev,
    OuterRef,
    Subquery,
    BooleanField,
    Q
)
from django.db.models.functions import Coalesce
from django.db.models import Case, When
from django.db.models import Subquery, Value
SUITABLY_HIGH_NUMBER = 99999999


class Competition(models.Model):
    name = models.CharField(unique=True, max_length=16)
    theme = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    round_started_at = models.DateTimeField(default=None, null=True)
    started = models.BooleanField(default=False)
    owner = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="created_competition"
    )
    current_meme = models.ForeignKey(
        "Meme", null=True, on_delete=models.SET_NULL, related_name="current", blank=True
    )
    winning_meme = models.ForeignKey(
        "Meme",
        null=True,
        on_delete=models.SET_NULL,
        related_name="won_competition",
        blank=True,
    )
    tiebreaker = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    timer_active = models.BooleanField(default=False)

    def start_competition(self):
        self.started = True
        self.save()


    def top_memes(self):
        return (
            self.memes.filter(competition=self)
            .annotate(
                vote_count=Count("votes"),
                total=Sum("votes__score"),
                distinct_votes=Count("votes__participant", distinct=True),
            )
            .annotate(
                vote_score=Case(
                    When(distinct_votes=0, then=Value(0.0)),
                    default=F("total") / F("distinct_votes"),
                    output_field=FloatField(),
                )
            )
            .order_by("-vote_score")
        )


    def tying_memes(self):
        top_meme_subquery = (
            self.top_memes()
            .annotate(count=Count("id"))
            .order_by("-count")
            .values("vote_score")[:1]
        )

        return (
            self.memes.filter(competition=self)
            .annotate(
                vote_count=Count("votes"),
                total=Sum("votes__score"),
                distinct_votes=Count("votes__participant", distinct=True),
            )
            .annotate(
                vote_score=Case(
                    When(distinct_votes=0, then=Value(0.0)),
                    default=F("total") / F("distinct_votes"),
                    output_field=FloatField(),
                )
            )
            .filter(vote_score=Subquery(top_meme_subquery))
            .values()
        )

    @property
    def num_memes(self):
        return self.memes.count()

    @property
    def num_participants(self):
        return self.participants.count()

    @property
    def sorted_participants(self):
        return self.participants.order_by("-active")

    @property
    def num_uploaders(self):
        return self.memes.values("participant").distinct().count()

    @property
    def num_voters(self):
        return self.votes.values("participant").distinct().count()

    @property
    def meme_ctr(self):
        return self.seen_memes.count()

    @property
    def has_updates_within_last_24_hours(self):
        return self.updated_at >= timezone.now() - timezone.timedelta(hours=1)


    def avg_meme_score(self):
        avg_rating = (
            self.memes.filter(votes__isnull=False)
            .aggregate(avg_score=Coalesce(Avg("votes__score"), 0.0))["avg_score"]
        )
        
        return round(avg_rating, 2) if avg_rating is not None else 0.0


    def avg_vote_time(self):
        avg_time = (
            self.votes
            .annotate(
                voting_duration=ExpressionWrapper(
                    F("created_at") - F("started_at"),
                    output_field=FloatField(),
                )
            )
            .aggregate(avg_time=Sum("voting_duration") / Count("id"))["avg_time"]
        )
        
        return round(avg_time, 2) if avg_time is not None else 0.0


    def get_avg_score_given_extrema(self):
        result = (
            self.votes
            .values("participant__name")
            .annotate(
                avg_score_given=ExpressionWrapper(
                    Avg("score"), output_field=FloatField()
                ),
            )
            .order_by("-avg_score_given", "avg_score_given")
        )

        highest_result = result.first()
        lowest_result = result.last()

        highest = {
            "participant": highest_result["participant__name"],
            "score": round(highest_result["avg_score_given"], 2),
        } if highest_result else {"participant": "No one", "score": 0.0}

        lowest = {
            "participant": lowest_result["participant__name"],
            "score": round(lowest_result["avg_score_given"], 2),
        } if lowest_result else {"participant": "No one", "score": 0.0}

        return {"highest": highest, "lowest": lowest}


    def highest_avg_score_received(self):
        participants = self.participants.filter(memes__votes__isnull=False).distinct()

        # Calculate the mean score for each participant
        participants = participants.annotate(mean_score=Avg("memes__votes__score"))

        # Retrieve the participant with the highest average score
        highest_score_participant = participants.order_by("-mean_score").first()

        if highest_score_participant:
            return {
                "participant": highest_score_participant.name,
                "score": round(highest_score_participant.mean_score, 2),
            }

        return {"participant": "No one", "score": 0.0}


    def highest_memes_submitted(self):
        participant_with_most_memes = (
            self.participants.annotate(
                num_memes=Count('memes', distinct=True)
            )
            .order_by('-num_memes')
            .values('name', 'num_memes')
            .first()
        )

        if participant_with_most_memes:
            return {
                "participant": participant_with_most_memes["name"],
                "num_memes": participant_with_most_memes["num_memes"],
            }

        return {"participant": "No one", "num_memes": 0}


    def get_avg_vote_time_extrema(self):
        participants_with_avg_time = (
            self.participants
            .annotate(
                avg_vote_time=ExpressionWrapper(
                    Avg(Case(
                        When(votes__voting_time__gt=0, then=F('votes__voting_time')),
                        default=Value(0),
                        output_field=FloatField()
                    )),
                    output_field=FloatField()
                )
            )
            .order_by("-avg_vote_time")
            .values("name", "avg_vote_time")
        )

        highest_result = participants_with_avg_time.first()
        lowest_result = participants_with_avg_time.last()

        highest_result = {
            "participant": highest_result["name"],
            "vote_time": round(highest_result["avg_vote_time"], 2)
        } if highest_result else {"participant": 'No one', "vote_time": 0.0}

        lowest_result = {
            "participant": lowest_result["name"],
            "vote_time": round(lowest_result["avg_vote_time"], 2)
        } if lowest_result else {"participant": 'No one', "vote_time": 0.0}

        return {"highest": highest_result, "lowest": lowest_result}

    def lowest_avg_own_memes(self):
        lowest_avg_participant = (
            self.participants.annotate(
                avg_score=Coalesce(
                    Avg(
                        ExpressionWrapper(F("votes__score"), output_field=FloatField()),
                        filter=Case(
                            When(votes__meme__participant=F("id"), then=True),
                            default=False,
                            output_field=BooleanField(),
                        ),
                    ),
                    # use a high number here to not assign this to any participants
                    # that didnt submit memes or didnt vote on their own memes
                    10.0,
                )
            )
            .order_by("avg_score")
            .first()
        )

        if lowest_avg_participant:
            return {
                "participant": lowest_avg_participant.name,
                "score": round(lowest_avg_participant.avg_score, 2),
            }

        return {"participant": "No one", "score": 0.0}


    def avg_vote_on_own_memes(self):
        # the average score each participant gave to their own memes
        # ensure participants have voted in this competition before continuing
        if not (self.num_voters and self.num_memes):
            return 0.0

        own_votes = self.votes.filter(meme__participant=F("participant"))
        own_votes_aggregate = own_votes.aggregate(
            total_score=Sum("score"), num_votes=Count("id")
        )
        # Calculate the average score participants gave to their own memes in the competition
        comp_total_avg = (
            (own_votes_aggregate["total_score"] / own_votes_aggregate["num_votes"])
            if own_votes_aggregate["num_votes"]
            else 0.0
        )

        return round(comp_total_avg, 2)

    def __str__(self):
        return f"Competition {self.theme} ({self.name})"
