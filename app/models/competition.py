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
)
from django.db.models.functions import Coalesce
from django.db.models import Case, When

from app.tasks import timer_advance_competition

SUITABLY_HIGH_NUMBER = 99999999


class Competition(models.Model):
    name = models.CharField(unique=True, max_length=16)
    theme = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    round_started_at = models.DateTimeField(default=None, null=True, blank=True)
    started = models.BooleanField(default=False)
    owner = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="created_competition"
    )
    current_meme = models.ForeignKey(
        "Meme", null=True, on_delete=models.SET_NULL, related_name="current", blank=True
    )
    __original_current_meme = None

    winning_meme = models.ForeignKey(
        "Meme",
        null=True,
        on_delete=models.SET_NULL,
        related_name="won_competition",
        blank=True,
    )
    tiebreaker = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    timer_task_id = models.CharField(max_length=765, unique=True, null=True, blank=True)
    with_timer = models.BooleanField(default=False)
    timer_timeout = models.PositiveIntegerField(default=15, blank=True)

    def __init__(self, *args, **kwargs):
        super(Competition, self).__init__(*args, **kwargs)
        self.__original_current_meme = self.current_meme

    def save(self, force_insert=False, force_update=False, *args, **kwargs):

        if self.with_timer:
            # if current_meme is set and it is different to the previous current_meme
            # start the voting timer
            if self.current_meme and self.current_meme != self.__original_current_meme:
                timer_task = timer_advance_competition.apply_async(
                    args=[self.id], 
                    countdown=self.timer_timeout, 
                    expiration=60,
                    queue="voting_timer_queue"
                )
                self.timer_task_id = timer_task.task_id
            # if we dont have a current meme but we still have a timer
            # that timer must be revoked
            elif not self.current_meme and self.timer_task_id:
                from app.utils import revoke_competition_timer
                revoke_competition_timer(self)

        super(Competition, self).save(force_insert, force_update, *args, **kwargs)
        self.__original_current_meme = self.current_meme

    def start_competition(self):
        self.started = True
        self.save()

    @property
    def ordered_memes(self):
        return (
            self.memes.filter(competition=self)
            .annotate(vote_count=Count("votes"), total=Sum("votes__score"))
            .annotate(
                vote_score=Coalesce(F("total") / Count("votes", distinct=True), 0.0)
            )
            .order_by("-vote_score")
        )

    @property
    def top_memes(self):
        top_meme = self.ordered_memes.first()
        return self.ordered_memes.filter(vote_score=top_meme.vote_score)

    @property
    def is_tie(self):
        top_meme = self.ordered_memes.first()
        if top_meme:
            return (
                len(self.ordered_memes.filter(vote_score=top_meme.real_avg_score)) > 1
            )
        return False

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

    @property
    def avg_meme_score(self):
        result = self.memes.aggregate(
            avg_rating=Coalesce(models.Avg("votes__score"), 0.0)
        )["avg_rating"]
        if result:
            return round(result, 2)
        return 0

    @property
    def avg_vote_time(self):
        avg_time = 0
        for v in self.votes.all():
            avg_time += v.voting_time

        if avg_time:
            avg_time /= len(self.votes.all())
            avg_time = round(avg_time, 2)
        return avg_time

    @property
    def highest_avg_score_given(self):
        result = (
            self.votes.values("participant__name")
            .annotate(avg_score_given=Avg("score"))
            .order_by("-avg_score_given")
            .first()
        )
        if result:
            return {
                "participant": result["participant__name"],
                "score": round(result["avg_score_given"], 2),
            }
        return {"participant": "No one", "score": 0.0}

    @property
    def lowest_avg_score_given(self):
        result = (
            self.votes.values("participant__name")
            .annotate(avg_score_given=Avg("score"))
            .order_by("-avg_score_given")
            .last()
        )
        if result:
            return {
                "participant": result["participant__name"],
                "score": round(result["avg_score_given"], 2),
            }
        return {"participant": "No one", "score": 0.0}

    @property
    def highest_avg_score_received(self):
        if len(self.votes.all()):
            participants = self.participants.filter(
                memes__votes__isnull=False
            ).distinct()
            # Calculate the mean score for each participant
            participants = participants.annotate(mean_score=Avg("memes__votes__score"))

            # Calculate the standard deviation of scores for each participant
            participants = participants.annotate(
                score_stddev=StdDev("memes__votes__score")
            )

            # Calculate the weighted score for each participant with penalization
            participants = participants.annotate(
                penalization_factor=ExpressionWrapper(
                    Count("memes") / self.num_memes, output_field=FloatField()
                ),
                weighted_score=ExpressionWrapper(
                    (F("mean_score") - (F("score_stddev")) * F("penalization_factor")),
                    output_field=FloatField(),
                ),
            )
            # Retrieve the participant with the highest weighted score
            highest_score_participant = participants.order_by("-weighted_score").first()
            if highest_score_participant:
                return {
                    "participant": highest_score_participant.name,
                    "score": round(highest_score_participant.weighted_score, 2),
                }
        return {"participant": "No one", "score": 0.0}

    @property
    def highest_memes_submitted(self):
        result = (
            self.memes.values("participant__name")
            .annotate(num_memes=Count("id"))
            .order_by("-num_memes")
            .first()
        )
        if result:
            return {
                "participant": result["participant__name"],
                "num_memes": result["num_memes"],
            }
        return {"participant": "No one", "num_memes": 0}

    @property
    def highest_avg_vote_time(self):
        if len(self.votes.all()):
            highest_avg = 0
            participant = None
            for p in self.participants.all():
                if p.avg_vote_time > highest_avg:
                    highest_avg = p.avg_vote_time
                    participant = p

            return {"participant": participant.name, "vote_time": round(highest_avg, 2)}
        return {"participant": "No one", "vote_time": 0.0}

    @property
    def lowest_avg_vote_time(self):
        # pretty gross but it works
        # blame django for not letting you use computed properties in queries
        if len(self.votes.all()):
            lowest_avg = SUITABLY_HIGH_NUMBER
            participant = None
            for p in self.participants.all():
                if p.avg_vote_time < lowest_avg and p.avg_vote_time > 0:
                    lowest_avg = p.avg_vote_time
                    participant = p

            if participant:
                return {
                    "participant": participant.name,
                    "vote_time": round(lowest_avg, 2),
                }

        return {"participant": "No one", "vote_time": 0.0}

    @property
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
                "score": round(lowest_avg_participant.avg_score or 0, 2),
            }
        return {"participant": "No one", "score": 0.0}

    @property
    def avg_vote_on_own_memes(self):
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
