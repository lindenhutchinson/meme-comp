# emoji_tags.py
from django import template

register = template.Library()


@register.inclusion_tag("tags/snackbar.html")
def snackbar():
    return {}

@register.inclusion_tag("tags/comp-card.html")
def comp_card(user, participant, competition):
    return {"user": user, "competition": competition, "participant": participant}


@register.inclusion_tag("tags/comp-waiting.html")
def comp_waiting(participant, competition):
    return {"participant": participant, "competition": competition}


@register.inclusion_tag("tags/comp-voting.html")
def comp_voting(competition):
    return {"competition": competition}


@register.inclusion_tag("tags/comp-finished.html")
def comp_finished(top_meme, competition):
    return {"competition": competition, "top_meme": top_meme}


@register.inclusion_tag("tags/comp-tiebreaker.html")
def comp_tiebreaker(competition):
    return {"competition": competition}


@register.inclusion_tag("tags/timer.html")
def comp_timer(time_limit):
    return {"time_limit": time_limit}

@register.inclusion_tag("tags/timer-bar-div.html")
def timer_bar_div(timeout, timer_enabled):
    return {"timeout": timeout, "timer_enabled":timer_enabled}

@register.inclusion_tag("tags/event-log-offcanvas.html")
def event_log_offcanvas(competition):
    return {"competition":competition}