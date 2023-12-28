from django import template
from app.models import Participant
register = template.Library()

@register.inclusion_tag('ws_tags/participant_li.html')
def participant_li(participant_id):
    participant = Participant.objects.get(id=participant_id)
    return {
        'participant':participant
    }

@register.inclusion_tag('ws_tags/winning_meme_div.html')
def winning_meme_div(competition):
    return {
        'winning_meme':competition.winning_meme
    }

@register.inclusion_tag('ws_tags/comp_results_div.html')
def comp_results_div(competition):
    return {
        'competition':competition
    }

@register.inclusion_tag('ws_tags/emoji_div.html')
def emoji_div():
    return {}
