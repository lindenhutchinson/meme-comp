from django.db import models


class Vote(models.Model):
    VOTE_CHOICES = [
        (1, "1 - Terrible"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Good"),
        (5, "5 - Excellent"),
    ]

    meme = models.ForeignKey('Meme', on_delete=models.CASCADE)
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE)
    score = models.IntegerField(choices=VOTE_CHOICES)

    def __str__(self):
        return f"{self.participant} voted {self.score} for {self.meme}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['participant', 'meme'], name='participant_meme')
        ]
