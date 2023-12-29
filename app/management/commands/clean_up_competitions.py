from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Competition


class Command(BaseCommand):
    help = "Delete competitions without updates in the last 24 hours"

    def handle(self, *args, **options):
        competitions = Competition.objects.all()
        delete_ctr = 0
        for competition in competitions:
            if not competition.has_updates_within_last_24_hours:
                competition.delete()
                delete_ctr += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Competitions cleanup completed successfully. Deleted {delete_ctr}"
            )
        )
