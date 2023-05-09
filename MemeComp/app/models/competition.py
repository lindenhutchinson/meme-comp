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
    
    @property
    def num_memes(self):
        return self.memes.count()

    def start_competition(self):
        self.started = True
        self.save()

    def __str__(self):
        return f"Competition {self.id} ({self.theme}) {self.name}"
