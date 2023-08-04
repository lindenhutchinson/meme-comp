from django.db import models
from django.db.models import Avg

class Participant(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='participants')
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    @property
    def num_memes(self):
        return self.memes.count()
    
    @property
    def top_meme(self):
        sorted_memes = sorted(self.memes.all(), key=lambda meme: meme.avg_score, reverse=True)
        return sorted_memes[0] if sorted_memes else None


    @property
    def avg_rating_given(self):
        rating =  self.votes.aggregate(avg_rating_given=Avg('score')).get('avg_rating_given') or 0
        return round(rating, 2)

    @property
    def avg_vote_time(self):
        total = 0
        for v in self.votes.all():
            total += v.voting_time

        return round(total / self.votes.count(), 2) if self.votes.count() else 0

    @property
    def avg_meme_score(self):
        meme_score = self.memes.aggregate(avg_meme_score=Avg('votes__score')).get('avg_meme_score') or 0
        return round(meme_score, 2)

    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['user', 'competition'], name='competition_user')
    ]

