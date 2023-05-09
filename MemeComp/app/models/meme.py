from django.db import models
from django.utils import timezone


class Meme(models.Model):
    image = models.ImageField(upload_to='memes')
    created_at = models.DateTimeField(default=timezone.now)
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='memes')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE, related_name='memes')

    def __str__(self):
        return f'Meme {self.id} by {self.participant.name}'
