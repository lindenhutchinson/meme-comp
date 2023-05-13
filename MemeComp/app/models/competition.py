from django.db import models
from django.utils import timezone

class Competition(models.Model):
    name = models.CharField(unique=True, max_length=16)
    theme = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    started = models.BooleanField(default=False)
    owner = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name="created_competition"
    )
    current_meme = models.ForeignKey(
        'Meme', null=True, on_delete=models.SET_NULL, related_name="current"
    )
    finished = models.BooleanField(default=False)
    
    @property
    def num_memes(self):
        return self.memes.count()

    def start_competition(self):
        self.started = True
        self.save()

    @property
    def num_participants(self):
        return self.participants.count()
    
    @property
    def num_uploaders(self):
        return self.memes.values('participant').distinct().count()

    @property
    def num_voters(self):
        return self.votes.values('participant').distinct().count()

    @property
    def meme_ctr(self):
        return self.seen_memes.count()


    def __str__(self):
        return f"Competition {self.id} ({self.theme}) {self.name}"
