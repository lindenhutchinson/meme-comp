from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg, Count, F, Max, Min, Q, Case, When, FloatField

class User(AbstractUser):
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="app_users",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        verbose_name="groups",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="app_users",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self):
        return self.username

    def shares_comp_with(self, user):
        return self.participants.filter(
            Q(competition__participants__user=user)
        ).exists()
    
    # Property to get the total number of competitions the user participated in.
    @property
    def total_competitions(self):
        return self.participants.count()

    # Property to get the total number of memes the user has submitted.
    @property
    def total_memes(self):
        return self.memes.count()
    
    @property
    def total_votes(self):
        return self.votes.count()

    # Property to get the total average vote given by the user.
    @property
    def total_avg_vote_given(self):
        avg_vote_given = self.votes.aggregate(avg_score=Avg('score')).get('avg_score') or 0
        return round(avg_vote_given, 2)

    # Property to get the total average meme score of all memes submitted by the user.
    @property
    def total_avg_vote_received(self):
        avg_vote_received = self.memes.aggregate(avg_score=Avg('votes__score')).get('avg_score') or 0
        return round(avg_vote_received, 0)

    @property
    def total_avg_vote_received_from_self(self):
        avg_own_vote = self.memes.filter(votes__user=self).aggregate(avg_score=Avg('votes__score')).get('avg_score') or 0
        
        return round(avg_own_vote, 2)

    # Property to get the total voting time for all the user's votes in minutes
    @property
    def total_voting_time(self):
        '''
        in seconds
        '''
        voting_time = sum(v.voting_time for v in self.votes.all())
        # get the time in minutes
        return round(voting_time, 2)
    
    @property
    def total_avg_voting_time(self):
        avg_voting_time = sum(v.voting_time for v in self.votes.all()) / (self.votes.count() or 1)
        return round(avg_voting_time, 2)
    
    # Property to get the number of competitions won by the user.
    @property
    def competitions_won(self):
        win_ctr = 0
        for participant in self.participants.all():
            if participant.competition.winning_meme and participant.competition.winning_meme.user == self:
                win_ctr +=1

        return win_ctr
    # Property to get the user's library of memes.
    @property
    def meme_library(self):
        return self.memes.all().filter(competition__finished=True).order_by('-created_at')

    # Property to get the highest average meme score given by the user.
    @property
    def highest_rated_user(self):
        return User.objects.annotate(
            avg_score=Avg(
                Case(
                    When(
                        memes__votes__user=self,
                        then=F('memes__votes__score')
                    ),
                    output_field=FloatField()
                )
            )
        ).filter(
            memes__votes__user=self
        ).exclude(id=self.id).order_by('-avg_score').first()
    
    # Property to get the user who the current user has rated their memes the highest.
    @property
    def highest_user_rated_by(self):
        return User.objects.annotate(
            avg_score_received=Avg(
                Case(
                    When(
                        memes__user=self,
                        then=F('memes__votes__score')
                    ),
                    output_field=FloatField()
                )
            )
        ).filter(
            memes__user=self
        ).exclude(id=self.id).order_by('-avg_score_received').first()
