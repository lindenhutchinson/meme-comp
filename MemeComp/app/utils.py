from django.contrib.auth import get_user_model
import random
import string
from django.db.models import Sum
from .models import Competition, SeenMeme, Meme
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_channel_message(comp_name, consumer, data=None):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        comp_name, {"type": consumer, "data": data}
    )

def generate_random_string(length):
    """Generate a random string up to the given maximum length."""
    valid_chars = [c for c in string.ascii_letters if c not in ['l', 'I', 'i', 'O', 'o']]
    return ''.join(random.choice(valid_chars) for _ in range(length))


def get_current_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            pass
    return None

def set_next_meme_for_competition(competition_id):

    # Get the competition
    competition = Competition.objects.get(id=competition_id)

    # Get the list of all memes for the competition
    all_memes = competition.memes.all()

    # Get the list of seen memes for the competition
    seen_memes = SeenMeme.objects.filter(competition=competition).values_list('meme', flat=True)

    # Exclude the seen memes from the list of all memes
    available_memes = all_memes.exclude(id__in=seen_memes)

    # Select a random meme from the available memes
    if available_memes.exists():
        random_meme = random.choice(available_memes)
        # Set the competition's current_meme to the randomly selected meme
        competition.current_meme = random_meme

        # Create a SeenMeme object for the selected meme and competition
        seen_meme = SeenMeme.objects.create(meme=random_meme, competition=competition)
        seen_meme.save()
    else:
        competition.current_meme = None
    
    competition.save()

    return competition

def get_top_memes(competition_name):
    # Get the competition instance
    competition = Competition.objects.get(name=competition_name)

    # Aggregate the total vote scores for each meme in the competition
    memes = Meme.objects.filter(competition=competition)
    sorted_memes = sorted(memes, key=lambda meme: meme.total_score, reverse=True)

    # Order the memes by total score in descending order and get the top three
    results = [
        {
            'id':meme.id,
            'participant':meme.participant.name,
            'score':meme.total_score
        } for meme in sorted_memes
    ]
    return results