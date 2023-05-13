import os
from django.conf import settings
from django.db import models
from django.utils import timezone


class Meme(models.Model):
    image = models.ImageField(upload_to='memes')
    created_at = models.DateTimeField(default=timezone.now)
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='memes')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE, related_name='memes')

    def __str__(self):
        return f'Meme {self.id} by {self.participant.name}'
    
    def delete(self, *args, **kwargs):
        # Delete the associated file
        if self.image:
            # Get the file path
            file_path = os.path.join(settings.MEDIA_ROOT, str(self.image))

            # Delete the file if it exists
            if os.path.isfile(file_path):
                os.remove(file_path)

        super().delete(*args, **kwargs)

    @property
    def num_votes(self):
        return self.votes.count()
    
    @property
    def total_score(self):
        return self.votes.aggregate(models.Sum('score')).get('score__sum') or 0