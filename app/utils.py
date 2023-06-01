import re
from django.contrib.auth import get_user_model
import random
import string
from django.db.models import Sum
from .models import Competition, SeenMeme, Meme
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib import messages
from django.shortcuts import redirect

def redirect_and_flash_error(request, error):
    messages.error(request, error)
    return redirect('home')

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
        SeenMeme.objects.create(meme=random_meme, competition=competition)
    else:
        competition.current_meme = None
    
    competition.save()

    return competition

def get_top_meme(competition_name):
    # Get the competition instance
    competition = Competition.objects.get(name=competition_name)

    # Aggregate the total vote scores for each meme in the competition
    memes = Meme.objects.filter(competition=competition)

    sorted_memes = sorted(memes, key=lambda meme: meme.total_score/(len(meme.votes.all()) or 1), reverse=True)
    meme = sorted_memes[0]
    score = round(meme.total_score / (len(meme.votes.all()) or 1), 2)
    # Order the memes by total score in descending order and get the top three
    results = {
        'id':meme.id,
        'participant':meme.participant.name,
        'score': score
    }
    return results

def send_shame_message(comp_name, username):
    messages = [
        f"{username} thinks they're a hackerman.",
        f"{username} is trying to do something they shouldn't.",
        f"{username} is why we can't have nice things.",
        f"{username} used hack! It's not very effective...",
        f"Warning: {username} is attempting to break into the secret cookie jar.",
        f"Attention! {username} is testing their hacking skills.",
        f"Caution: {username} is attempting to hack their way to world domination.",
        f"Attention: {username} is currently experiencing technical difficulties in their hacking endeavours.",
        f"Error 404: {username}'s hacking skills not found. Please check your connection to the Matrix and try again.",
        f"Congratulations, {username}! You've been nominated for the 'Best Attempted Hack of the Year' award.",
        f"Warning: {username} is conducting a secret hacking mission.",
    ]
    message = random.choice(messages)
    send_channel_message(comp_name, 'update_shame', message)

def check_emoji_text(text):
    try:
        emoji = re.search(r'(\d{4,6})', f'{ord(text)}')
        emoji_text = chr(int(emoji.group(1)))
        return emoji_text or False
    except TypeError:
        return False

def do_advance_competition(competition):
    # attempt to get a random next meme for the competition
    competition = set_next_meme_for_competition(competition.id)

    if competition.current_meme:
    # if we were able to set a random meme, update the channel to show it on the page
        data = {
            'id':competition.current_meme.id,
            'num_memes':competition.num_memes,
            'ctr':competition.meme_ctr
        }
        send_channel_message(competition.name, 'next_meme', data)
    else:
        # if no meme was set, end the competition - update the channel to show the competition results info
        statistics = {
                'fastest_voter':f'{competition.lowest_avg_vote_time["participant"]} averaged {competition.lowest_avg_vote_time["vote_time"]} seconds per vote',
                'slowest_voter':f'{competition.highest_avg_vote_time["participant"]} averaged {competition.highest_avg_vote_time["vote_time"]} seconds per vote',
                'highest_score_given':f'{competition.highest_avg_score_given["participant"]} gave a {competition.highest_avg_score_given["score"]} average score',
                'lowest_score_given':f'{competition.lowest_avg_score_given["participant"]} gave a {competition.lowest_avg_score_given["score"]} average score',
                'most_submitted':f'{competition.highest_memes_submitted["participant"]} submitted {competition.highest_memes_submitted["num_memes"]} memes',
                'highest_avg_score':f'{competition.highest_avg_score_received["participant"]} received a {competition.highest_avg_score_received["score"]} weighted score',
                'avg_own_score':f'{competition.lowest_avg_own_memes["participant"]} gave themselves a {competition.lowest_avg_own_memes["score"]} average score',
                'avg_meme_score':competition.avg_meme_score,
                'avg_vote_time':competition.avg_vote_time,
        } if len(competition.votes.all()) else {}
        competition.finished = True
        competition.save()
        results = {}
        if len(competition.votes.all()):
            top_meme = get_top_meme(competition.name)
            results = {
                'top_meme':top_meme,
                'statistics':statistics
            }
        send_channel_message(competition.name, 'competition_results', results)