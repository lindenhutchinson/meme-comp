import os
import random
from django.conf import settings
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .utils import (
    is_broker_connected,
    num_votes_for_round,
    redis_lock,
    send_shame_message,
    set_next_meme_for_competition,
    send_channel_message,
)
from .models import Meme, Competition, Vote, Participant, SeenMeme
from .serializers import MemeSerializer
import time
from .tasks import do_advance_competition
from django.db import transaction
from django.db.utils import OperationalError
import sqlite3


@api_view(["DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def meme_delete(request, meme_id):
    # Retrieve the meme object
    meme = get_object_or_404(Meme, id=meme_id)
    competition = meme.competition
    # Verify if the authenticated user has a participant associated with the meme
    if meme.participant.user != request.user:
        # User is not authorized to delete the meme
        print(f"{request.user.username} attempted to delete the wrong meme")
        send_shame_message(competition, request.user.username)
        return Response(
            {"detail": "Delete your own memes, you donkey"},
            status=status.HTTP_403_FORBIDDEN,
        )

    meme.image.close()
    # Delete the file from the file system
    meme_image_path = os.path.join(settings.MEDIA_ROOT, meme.image.name)
    sanity_ctr = 0
    MAX_DELETE_ATTEMPTS = 10
    # images sometimes can't be deleted because they are open
    # keep trying to close the image.
    while os.path.exists(meme_image_path) and sanity_ctr < MAX_DELETE_ATTEMPTS:
        sanity_ctr += 1
        try:
            os.remove(meme_image_path)
        except PermissionError:
            print(f"Attempt to delete meme: {sanity_ctr}")
            meme.image.close()
            time.sleep(0.5)

    if sanity_ctr == MAX_DELETE_ATTEMPTS:
        return Response(
            {"detail": "Couldn't delete, try again"},
            status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
        )

    # Delete the meme
    meme.delete()
    # Update total memes count
    total_memes = competition.memes.count()
    send_channel_message(
        competition.name,
        "meme_uploaded",
        {"num_memes": total_memes, "num_uploaders": competition.num_uploaders},
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def meme_upload(request, comp_name):
    competition = get_object_or_404(Competition, name=comp_name)
    participant = Participant.objects.get(competition=competition, user=request.user)
    if not participant:
        print(f"{request.user.username} attempted an invalid upload")
        send_shame_message(competition.name, request.user.username)
        return Response(
            {"detail": "Smart guy aye? Try again buddy"},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = MemeSerializer(data=request.data)
    if serializer.is_valid():
        # these values are hidden inputs on the form that can be edited by the user on the page
        # dont really need these, but it's funny to catch someone trying that.
        if (
            serializer.validated_data["competition"] != competition
            or serializer.validated_data["participant"] != participant
        ):
            print(f"{request.user.username} attempted an invalid upload")
            send_shame_message(competition.name, request.user.username)
            return Response(
                {"detail": "You think you're so clever"},
                status=status.HTTP_403_FORBIDDEN,
            )

        meme_list = []
        for img in request.FILES.getlist("image"):
            meme = Meme.objects.create(
                image=img,
                competition=competition,
                participant=participant,
                user=request.user,
            )
            if meme:
                meme_list.append(meme.id)
            else:
                return Response(
                    {"detail": "Error uploading meme"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        competition.refresh_from_db()
        total_memes = competition.memes.count()
        send_channel_message(
            competition.name,
            "meme_uploaded",
            {"num_memes": total_memes, "num_uploaders": competition.num_uploaders},
        )
        return Response(meme_list, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


BREAK_TIE_SCORE = 0.001
VOTING_TIMEOUT_SECONDS = 10
TIMEOUT_VOTING_THRESHOLD = 0.5


@transaction.atomic
def check_and_start_timer(total_votes, competition):
    lock_key = f"advance_comp_task_lock_{competition.id}"
    with redis_lock(lock_key):
        # Refresh the competition instance to get the latest data within the transaction
        competition.refresh_from_db()
        # only start if a certain percentage of participants have voted
        voters_exceed_threshold = (
            total_votes / competition.num_participants
        ) >= TIMEOUT_VOTING_THRESHOLD
        # only start timer if workers are connected and it hasnt already started
        if (
            not competition.timer_active
            and voters_exceed_threshold
            # and is_broker_connected() - slow and unnecessary!
            # implemented so we dont add the task when the broker is down but whatever she'll be roight m8
        ):
            competition.timer_active = True
            competition.save()
            do_advance_competition.apply_async(
                args=[competition.id], countdown=VOTING_TIMEOUT_SECONDS, queue="memes"
            )

            send_channel_message(competition.name, "timer_start")


from django.db import transaction


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def meme_vote(request, comp_name):
    score = request.data.get("vote", BREAK_TIE_SCORE)
    meme_id = request.data.get("meme_id", False)

    competition = get_object_or_404(Competition, name=comp_name)
    participant = get_object_or_404(
        Participant, user=request.user, competition=competition
    )

    try:
        if meme_id:
            # If meme_id is set, this is a tiebreaker vote
            meme = get_object_or_404(Meme, id=meme_id)
        else:
            # If meme_id is not set, this is a regular vote
            meme = competition.current_meme

            if not meme:
                return Response(
                    {"detail": "Where's your meme?"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            score = int(score)
            if score < 0 or score > 5:
                send_shame_message(competition.name, request.user.username)
                return Response(
                    {"detail": "Bad Request"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        vote, created = Vote.objects.get_or_create(
            meme=meme,
            participant=participant,
            competition=competition,
            user=request.user,
            defaults={"score": score, "started_at": competition.round_started_at},
        )

        if not created:
            # If the vote already exists, update the score
            if meme_id:
                vote.score += random.random() * 0.0001
            else:
                vote.score = score
            vote.save()

        competition.refresh_from_db()
        round_votes = num_votes_for_round(competition)

        send_channel_message(competition.name, "meme_voted", round_votes)
        with transaction.atomic():
            if not competition.timer_active:
                check_and_start_timer(round_votes, competition)

        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)

    except OperationalError as e:
        print("oopsy doopsy locked database. it will probably still work in a bit")
        return Response(
            {"success": "maybe"},
            status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
        )
    except:
        # Handle other exceptions that may occur during the process
        return Response(
            {"detail": "Internal Server Error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def start_competition(request, comp_name):
    # Process the competition start request
    competition = get_object_or_404(Competition, name=comp_name)

    # Check if the request user is the owner of the competition
    if competition.owner != request.user:
        print(f"{request.user.username} attempted to start the competition")
        send_shame_message(competition.name, request.user.username)
        return Response(
            {"detail": "You are not authorized to start this competition."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # ensure competition hasn't already started
    if competition.started:
        return Response(
            {"detail": "You have already started this competition"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    competition = set_next_meme_for_competition(competition.id)
    if competition.current_meme:
        competition.started = True
        competition.save()
        data = {
            "id": competition.current_meme.id,
            "num_memes": competition.num_memes,
            "ctr": competition.meme_ctr,
        }
        send_channel_message(competition.name, "next_meme", data)
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(
            {"detail": "Cannot start a competition without any uploads."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def advance_competition(request, comp_name):
    # Process the competition advance request
    competition = get_object_or_404(Competition, name=comp_name)

    # Check if the request user is the owner of the competition
    if competition.owner != request.user:
        print(f"{request.user.username} attempted to advance the competition")
        send_shame_message(competition.name, request.user.username)
        return Response(
            {"detail": "You are not authorized to advance this competition."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not competition.started:
        return Response(
            {"detail": "You cannot advance a competition that hasn't started"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # disabled while timer might fail
    # only manually advance the competition is the timer hasnt already started
    # if competition.timer_active and is_broker_connected():
    #     return Response(status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

    do_advance_competition(competition.id)

    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def cancel_competition(request, comp_name):
    # Process the competition cancel request
    competition = get_object_or_404(Competition, name=comp_name)

    # Check if the request user is the owner of the competition
    if competition.owner != request.user:
        print(f"{request.user.username} attempted to cancel the competition")
        send_shame_message(competition.name, request.user.username)
        return Response(
            {"detail": "You are not authorized to cancel this competition."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not competition.started:
        return Response(
            {"detail": "The competition has not started yet."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # clear the relevant  fields
    competition.current_meme = None
    competition.started = False
    competition.finished = False
    competition.tiebreaker = False
    competition.timer_active = False
    competition.save()

    # delete the seen memes of the competition
    SeenMeme.objects.filter(competition=competition).delete()
    comp_memes = competition.memes.all()
    votes = Vote.objects.filter(meme__in=comp_memes)
    votes.delete()

    Participant.objects.filter(competition=competition).update(ready=False)
    # alert the channel that the competition has been cancelled
    send_channel_message(competition.name, "competition_cancelled")
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def readyup_participant(request, part_id):
    participant = get_object_or_404(Participant, id=part_id, user=request.user)
    if participant.competition.finished:
        return Response(
            {"detail": "The competition has already finished."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    participant.ready = True
    participant.save()

    send_channel_message(
        participant.competition.name,
        "participant_ready",
        {"is_ready": True, "part_id": participant.id},
    )
    return Response(status=status.HTTP_200_OK)
