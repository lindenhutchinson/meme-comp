

from functools import wraps

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from app.models.competition import Competition
from app.models.meme import Meme
from app.models.participant import Participant
from app.utils import send_shame_message


def with_comp(view_func):
    @wraps(view_func)
    def wrapper(request, comp_name, *args, **kwargs):
        competition = get_object_or_404(Competition, name=comp_name)
        kwargs['competition'] = competition
        return view_func(request, comp_name, *args, **kwargs)

    return wrapper

def with_meme(view_func):
    @wraps(view_func)
    def wrapper(request, meme_id, *args, **kwargs):
        meme = get_object_or_404(Meme, pk=meme_id)
        kwargs['meme'] = meme
        kwargs['competition'] = meme.competition
        return view_func(request, meme_id, *args, **kwargs)

    return wrapper

def as_comp_participant(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        competition = kwargs.get('competition')
        participant = Participant.objects.get(competition=competition, user=request.user)
        if not participant:
            send_shame_message(competition.name, request.user.username)
            return Response(
                {"detail": "Smart guy aye? Try again buddy"},
                status=status.HTTP_403_FORBIDDEN,
            )
        kwargs['participant'] = participant
        
        return view_func(request, *args, **kwargs)

    return wrapper

def as_meme_owner(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        meme = kwargs.get('meme')
        if meme and meme.user != request.user:
            send_shame_message(meme.competition, request.user.username)
            return Response(
                {"detail": "Access your own memes, you donkey"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)

    return wrapper

def as_comp_owner(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        competition = kwargs.get('competition')
        if competition and competition.owner != request.user:
            send_shame_message(competition.name, request.user.username)
            return Response(
                {"detail": "You are not authorized to access this competition."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)

    return wrapper

def with_comp_state(allowed_states):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            competition = kwargs.get('competition')
            if competition and competition.state not in allowed_states:
                return Response(
                    {"detail": f"The competition is not in the required state: {competition.state}."},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

def with_comp_memes(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        competition = kwargs.get('competition')
        if not competition.num_memes:
            return Response(
                {"detail": "Cannot start a competition without any memes."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return view_func(request, *args, **kwargs)

    return wrapper