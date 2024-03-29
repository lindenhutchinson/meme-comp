from django.utils import timezone
from django.db import models
import pytz


def convert_to_localtime(utctime, format="%A %d %b - %I:%M%p"):
    utc = utctime.replace(tzinfo=pytz.UTC)
    localtz = utc.astimezone(timezone.get_current_timezone())
    return localtz.strftime(format)


class CompetitionLog(models.Model):
    class CompActions(models.TextChoices):
        UPLOAD = "upload", "uploaded a meme"
        DELETE = "delete", "deleted a meme"
        CREATE = "create", "created the competition"
        JOIN = "join", "joined"
        START = "start", "started the competition"
        CANCEL = "cancel", "cancelled the competition"
        ADVANCE = "advance", "advanced the competition"
        SETTINGS = "settings", "updated the competition settings"
        VOTE = "vote", "voted"
        WON = "won", "won!"

    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="comp_logs")
    competition = models.ForeignKey(
        "Competition", on_delete=models.CASCADE, related_name="logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.CharField(choices=CompActions.choices, max_length=100)

    @property
    def label(self):
        return f"{self.user.username} {self.CompActions(self.event).label}"

    @property
    def timestamp_label(self):
        return convert_to_localtime(self.created_at, "%#I:%M:%S")
