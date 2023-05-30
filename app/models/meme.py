import os
from django.conf import settings
from django.db import models
from django.utils import timezone
from PIL import Image


class MemeManager(models.Manager):
    def create(self, **obj_data):
        meme =  super().create(**obj_data)
        
        # resize the image
        image = meme.image
        if not image.path.endswith('.gif'):
            with Image.open(image.path) as im:
                im.thumbnail((1000, 1000), Image.Resampling.BICUBIC)
                im.save(image.path)

        return meme
             

class Meme(models.Model):
    image = models.ImageField(upload_to='memes')
    created_at = models.DateTimeField(default=timezone.now)
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='memes')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE, related_name='memes')
    objects = MemeManager()
    
    def __str__(self):
        return f'Meme {self.id} by {self.participant.name}'       

    @property
    def num_votes(self):
        return self.votes.count()
    
    @property
    def total_score(self):
        return self.votes.aggregate(models.Sum('score')).get('score__sum') or 0
    
    @property
    def avg_score(self):
        score = self.votes.aggregate(models.Avg('score')).get('score__avg') or 0
        return round(score, 2)
