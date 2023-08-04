# emoji_tags.py
from django import template

register = template.Library()

@register.inclusion_tag('tags/comp-card.html')
def comp_card(user, competition):
    return {
        'user':user,
        'competition':competition
    }

@register.inclusion_tag('tags/comp-waiting.html')
def comp_waiting(participant, competition):
    return {
        'participant':participant,
        'competition':competition,
    }

@register.inclusion_tag('tags/comp-voting.html')
def comp_voting(competition):
    return {
        'competition':competition,
    }


@register.inclusion_tag('tags/comp-finished.html')
def comp_finished(top_meme, competition):
    return {
        'competition':competition,
        'top_meme':top_meme
    }


@register.inclusion_tag('tags/comp-tiebreaker.html')
def comp_tiebreaker(tying_memes, competition):
    return {
        'competition':competition,
        'tying_memes':tying_memes
    }
