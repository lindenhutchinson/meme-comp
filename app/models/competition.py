from django.db import models
from django.utils import timezone
from django.db.models import Avg, Count, ExpressionWrapper, Min, Max
from django.db.models.functions import Extract


class Competition(models.Model):
    name = models.CharField(unique=True, max_length=16)
    theme = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started = models.BooleanField(default=False)
    owner = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name="created_competition"
    )
    current_meme = models.ForeignKey(
        'Meme', null=True, on_delete=models.SET_NULL, related_name="current"
    )
    finished = models.BooleanField(default=False)
    
    def start_competition(self):
        self.started = True
        self.save()

    @property
    def num_memes(self):
        return self.memes.count()

    @property
    def num_participants(self):
        return self.participants.count()
    
    @property
    def sorted_participants(self):
        return self.participants.order_by('-active')
    
    @property
    def num_uploaders(self):
        return self.memes.values('participant').distinct().count()

    @property
    def num_voters(self):
        return self.votes.values('participant').distinct().count()

    @property
    def meme_ctr(self):
        return self.seen_memes.count()

    @property
    def has_updates_within_last_24_hours(self):
        return self.updated_at >= timezone.now() - timezone.timedelta(hours=1)

    @property
    def avg_meme_score(self):
        result = self.memes.aggregate(avg_rating=models.Avg('votes__score'))['avg_rating']
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
        result = self.votes.values('participant__name').annotate(
            avg_score_given=Avg('score')
        ).order_by('-avg_score_given').first()
        if result:
            return {
                'participant':result['participant__name'],
                'score':round(result['avg_score_given'], 2)
            }
        
    @property
    def lowest_avg_score_given(self):
        result = self.votes.values('participant__name').annotate(
            avg_score_given=Avg('score')
        ).order_by('-avg_score_given').last()
        if result:
            return {
                'participant':result['participant__name'],
                'score':round(result['avg_score_given'], 2)
            }

    @property
    def highest_avg_score_received(self):
        result = self.votes.values('meme__participant__name').annotate(
            avg_score_received=Avg('score')
        ).order_by('-avg_score_received').first()
        if result:
            return {
                'participant':result['meme__participant__name'],
                'score':round(result['avg_score_received'], 2)
            }
        return {}
    
    @property
    def highest_memes_submitted(self):
        result = self.memes.values('participant__name').annotate(
            num_memes=Count('id')
        ).order_by('-num_memes').first()
        if result:
            return {
                'participant': result['participant__name'],
                'num_memes': result['num_memes'],
            }
        return {}
        
    @property
    def highest_avg_vote_time(self):
        highest_avg = 0
        participant = None
        for p in self.participants.all():
            avg_vote_time = 0
            for v in p.votes.all():
                avg_vote_time += v.voting_time

            if avg_vote_time:
                avg_vote_time /= len(p.votes.all())
                if avg_vote_time > highest_avg:
                    highest_avg = avg_vote_time
                    participant = p.name

        return {
            'participant':participant, 
            'vote_time': round(highest_avg, 2)
        }
    @property
    def lowest_avg_vote_time(self):
        lowest_avg = 999999999999
        participant = None
        for p in self.participants.all():
            avg_vote_time = 0
            for v in p.votes.all():
                avg_vote_time += v.voting_time

            if avg_vote_time:
                avg_vote_time /= len(p.votes.all())
                if avg_vote_time < lowest_avg:
                    lowest_avg = avg_vote_time
                    participant = p.name

        return {
            'participant':participant, 
            'vote_time': round(lowest_avg, 2)
        }
    

    def __str__(self):
        return f"Competition {self.id} ({self.theme}) {self.name}"
