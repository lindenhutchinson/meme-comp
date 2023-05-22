from django.db import models
class SeenMeme(models.Model):
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name="seen_memes")
    meme = models.ForeignKey('Meme', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('competition', 'meme')