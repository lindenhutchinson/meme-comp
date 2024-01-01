
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from api.ws_actions import send_meme_uploaded, send_next_meme, create_competition_log
from app.tasks import delete_meme
from app.utils import (
    revoke_competition_timer,
    run_advance_competition,
    num_votes_for_round,
    send_shame_message,
    set_next_meme_for_competition,
)
from .ws_actions import send_channel_message
from app.models import Meme, Competition, Vote, SeenMeme, CompetitionLog
from .serializers import MemeSerializer
from api.wrappers import (
    as_comp_owner,
    as_comp_participant,
    as_meme_owner,
    with_comp,
    with_comp_memes,
    with_comp_state,
    with_meme
)




@api_view(["DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@with_meme
@as_meme_owner
@with_comp_state([Competition.CompState.UNSTARTED]) # todo - implement meme delete?
def meme_delete(request, meme_id, meme=None, competition=None):
    # delete the meme using celery, as
    delete_meme.apply_async(args=[meme_id])
    # Update total memes count
    create_competition_log(competition, request.user, CompetitionLog.CompActions.DELETE)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@with_comp
@as_comp_participant
def meme_upload(request, comp_name, competition=None, participant=None):
    serializer = MemeSerializer(data=request.data)
    if serializer.is_valid():
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

        meme_list_html = []
        for img in request.FILES.getlist("image"):
            meme = Meme.objects.create(
                image=img,
                competition=competition,
                participant=participant,
                user=request.user,
            )
            if meme:
                meme_html = render_to_string(
                    "ws_tags/meme_image_div.html", {"meme": meme}
                )
                meme_list_html.append(meme_html)
            else:
                return Response(
                    {"detail": "Error uploading meme"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        send_meme_uploaded(competition)
        create_competition_log(
            competition, request.user, CompetitionLog.CompActions.UPLOAD
        )

        return Response(
            {"memes_html": "".join(meme_list_html)}, status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@with_comp
@with_comp_memes
@with_comp_state([Competition.CompState.STARTED])
@as_comp_participant
def meme_vote(request, comp_name, competition=None, participant=None):
    score = request.data.get("vote", 0)
    try:
        score = int(score)
        # ( todo - set change this to settings values)
        if score < 0 or score > 5:
            raise ValueError
    except Exception as e:
        send_shame_message(competition.name, request.user.username)
        return Response({"detail": "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)

    if not competition.current_meme:
        # if the current meme doesnt exist
        # that probably means the user clicked the vote button right as the comp finished
        return Response({"detail": "Too late"}, status=status.HTTP_417_EXPECTATION_FAILED)
    
    vote, created = Vote.objects.get_or_create(
        meme=competition.current_meme,
        participant=participant,
        competition=competition,
        user=request.user,
        defaults={"score": score, "started_at": competition.round_started_at},
    )
    if created:
        # only create the log the first time the user votes
        create_competition_log(
            competition, request.user, CompetitionLog.CompActions.VOTE
        )
        # likewise - only send the channel update the first time as well
        round_votes = num_votes_for_round(competition)
        send_channel_message(competition.name, "memeVoted", round_votes)
        return Response({"success": True}, status=status.HTTP_201_CREATED)
    else:
        vote.score = score
        vote.save()
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@with_comp
@as_comp_owner
@with_comp_state([Competition.CompState.UNSTARTED])
def start_competition(request, comp_name, competition=None):
    competition = set_next_meme_for_competition(competition)
    competition.refresh_from_db()
    if competition.current_meme:
        competition.state = Competition.CompState.STARTED
        competition.save()
        send_next_meme(competition)
        return Response(status=status.HTTP_200_OK)

    else:
        return Response(
            {"detail": "Where'd the current meme go?"},
            status=status.HTTP_400_BAD_REQUEST,
        )



@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@with_comp
@as_comp_owner
@with_comp_state([Competition.CompState.STARTED])
def advance_competition(request, comp_name, competition=None):

    run_advance_competition(competition)

    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
@with_comp
@as_comp_owner
@with_comp_state([Competition.CompState.STARTED, Competition.CompState.FINISHED])
def cancel_competition(request, comp_name, competition=None):
    # clear the relevant  fields
    competition.current_meme = None
    competition.winning_meme = None
    competition.state = Competition.CompState.UNSTARTED
    revoke_competition_timer(competition)
    competition.save()

    # delete the seen  memes of the competition
    SeenMeme.objects.filter(competition=competition).delete()
    Vote.objects.filter(competition=competition).delete()

    # alert the channel that the competition has been cancelled
    send_channel_message(competition.name, "competitionCancelled")
    create_competition_log(competition, request.user, CompetitionLog.CompActions.CANCEL)

    return Response(status=status.HTTP_200_OK)
