from celery import shared_task



@shared_task(ignore_result=True)
def timer_advance_competition(competition_id):
    from .models import Competition
    from app.utils import run_advance_competition

    competition = Competition.objects.get(id=competition_id)
    run_advance_competition(competition, as_task=True)
   