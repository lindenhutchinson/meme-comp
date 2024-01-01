from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
import os

@shared_task(ignore_result=True)
def timer_advance_competition(competition_id):
    from .models import Competition
    from app.utils import run_advance_competition

    competition = Competition.objects.get(id=competition_id)
    run_advance_competition(competition, as_task=True)
   



@shared_task(bind=True, max_retries=10, retry_backoff=True)
def delete_meme(self, meme_id):
    from app.models import Meme
    from api.ws_actions import send_meme_uploaded


    try:
        meme = Meme.objects.get(pk=meme_id)
        meme.image.close()
        meme_image_path = os.path.join(settings.MEDIA_ROOT, meme.image.name)
        os.remove(meme_image_path)
        meme.delete()
        send_meme_uploaded(meme.competition)

    except Meme.DoesNotExist:
        # Handle case where meme doesn't exist
        return {"status": "failed", "detail": "Meme not found"}
    except PermissionError:
        print(f"Attempt to delete meme: {self.request.retries}")
        meme.image.close()
        raise self.retry()
    except MaxRetriesExceededError:
        # Handle the case where the file couldn't be deleted after multiple attempts
        return {"status": "failed", "detail": "Couldn't delete, try again"}
    
    return {"status": "success", "detail": "Meme deleted successfully"}
