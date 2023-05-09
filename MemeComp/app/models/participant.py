from django.db import models

class Participant(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='participants')
    
    def __str__(self):
        return self.name
    
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['user', 'competition'], name='competition_user')
    ]

