from django.db import models
import datetime

class Vote(models.Model):
    VOTE_CHOICES = [
        (0, "0 - Just Awful"),
        (1, "1 - Terrible"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Good"),
        (5, "5 - Excellent"),
    ]

    meme = models.ForeignKey('Meme', on_delete=models.CASCADE, related_name="votes")
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE, related_name="votes")
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name="votes")
    score = models.IntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(default=None)

    @property
    def voting_time(self):
        # return how long the participant took to cast their vote, in seconds
        return int(self.created_at.timestamp()) - int(self.started_at.timestamp())

    def __str__(self):
        return f"{self.participant} voted {self.score} for {self.meme}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['participant', 'meme'], name='participant_meme')
        ]
