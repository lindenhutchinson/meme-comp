import os
import random
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .utils import get_top_meme, send_shame_message, set_next_meme_for_competition, send_channel_message
from .models import Meme, Competition, Vote, Participant, SeenMeme
from .serializers import MemeSerializer
import re

@api_view(['DELETE'])
@authentication_classes([SessionAuthentication])  # Use appropriate authentication classes
@permission_classes([IsAuthenticated])  # Use appropriate permission classes
def meme_delete(request, meme_id):
    # Retrieve the meme object
    meme = get_object_or_404(Meme, id=meme_id)
    competition = meme.competition
    # Verify if the authenticated user has a participant associated with the meme
    if meme.participant.user != request.user:
        # User is not authorized to delete the meme
        return Response({"detail": "Delete your own memes, you donkey"}, status=status.HTTP_403_FORBIDDEN)

    meme.image.close()
    # Delete the file from the file system
    meme_image_path = os.path.join(settings.MEDIA_ROOT, meme.image.name)
    sanity_ctr = 0
    while os.path.exists(meme_image_path) and sanity_ctr < 50:
        sanity_ctr +=1
        try:
            os.remove(meme_image_path)
        except PermissionError:
            meme.image.close()
            
    if sanity_ctr == 50:
        return Response({"detail": "Couldn't delete, try again"}, status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

    # Delete the meme
    meme.delete()
    # Update total memes count
    total_memes = competition.memes.count()
    send_channel_message(competition.name, 'update_uploaded', {
        'num_memes':total_memes,
        'num_uploaders':competition.num_uploaders
    })
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])  # Use appropriate authentication classes
@permission_classes([IsAuthenticated])  # Use appropriate permission classes
def meme_upload(request, comp_name):
    competition = get_object_or_404(Competition, name=comp_name)
    participant = Participant.objects.get(competition=competition, user=request.user)
    if not participant:
        send_shame_message(competition.name, request.user.username)
        return Response({'detail':"Smart guy aye? Try again buddy"}, status=status.HTTP_403_FORBIDDEN)
    serializer = MemeSerializer(data=request.data)
    if serializer.is_valid():
        # these values are hidden inputs on the form that can be edited by the user on the page
        # let them know I'm onto their tricks :3
        if serializer.validated_data['competition'] != competition or serializer.validated_data['participant'] != participant:
            send_shame_message(competition.name, request.user.username)
            return Response({'detail':"You think you're so clever"}, status=status.HTTP_403_FORBIDDEN)
        
        meme_list = []
        for img in request.FILES.getlist('image'):
            meme = Meme.objects.create(
                image=img,
                competition=competition,
                participant=participant
            )
            meme_list.append(meme.id)

        competition.refresh_from_db()
        total_memes = competition.memes.count()
        send_channel_message(competition.name, 'update_uploaded', {
            'num_memes':total_memes,
            'num_uploaders':competition.num_uploaders
        })
        return Response(meme_list, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def start_competition(request, comp_name):
    # Process the competition start request
    competition = get_object_or_404(Competition, name=comp_name)

    # Check if the request user is the owner of the competition
    if competition.owner != request.user:
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
            'id':competition.current_meme.id,
            'num_memes':competition.num_memes,
            'ctr':competition.meme_ctr
        }
        send_channel_message(competition.name, 'next_meme', data)
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(
            {'detail': "Cannot start a competition without any uploads."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def advance_competition(request, comp_name):  
    # Process the competition advance request
    competition = get_object_or_404(Competition, name=comp_name)

    # Check if the request user is the owner of the competition
    if competition.owner != request.user:
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
        # if no meme was set, end the competition - update the channel to show the competition results info
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

    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def cancel_competition(request, comp_name):
    # Process the competition cancel request
    competition = get_object_or_404(Competition, name=comp_name)

    # Check if the request user is the owner of the competition
    if competition.owner != request.user:
        send_shame_message(competition.name, request.user.username)
        return Response(
            {"detail": "You are not authorized to cancel this competition."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Set the competition as started, set the current meme, etc.
    if not competition.started:
        return Response(
            {"detail": "The competition has not started yet."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )

    # clear the relevant  fields
    competition.current_meme = None 
    competition.started = False
    competition.finished = False
    competition.save()  

    # delete the seen memes of the competition
    SeenMeme.objects.filter(competition=competition).delete()   
    comp_memes = competition.memes.all()
    votes = Vote.objects.filter(meme__in=comp_memes)
    votes.delete()       

    # alert the channel that the competition has been cancelled
    send_channel_message(competition.name, 'cancel_competition')
    return Response(status=status.HTTP_200_OK)           


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def meme_vote(request, comp_name):
    score_text = request.data.get('vote')
    competition = get_object_or_404(Competition, name=comp_name)
    participant = get_object_or_404(Participant, user=request.user, competition=competition)
    meme = competition.current_meme
    
    try:
        score = int(score_text)
    except TypeError:
        send_shame_message(competition.name, request.user.username)
        return Response({'detail':'Bad Request'}, status=status.HTTP_400_BAD_REQUEST)

    if score < 0 or score > 5:
        send_shame_message(competition.name, request.user.username)
        return Response({'detail':'Bad Request'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        vote = Vote.objects.get(meme=meme, participant=participant, competition=competition)
        vote.score = score
        vote.save()
    except Vote.DoesNotExist:
        # create a vote using the meme, participant and the given score
        # also set "started_at" to when the competition last updated
        # this will allow calculations of how long the user took to vote
        vote = Vote.objects.create(competition=competition, meme=meme, participant=participant, score=score, started_at=competition.updated_at)
        total_votes = Vote.objects.filter(meme_id=meme.id).aggregate(total_votes=Count('id'))
        send_channel_message(competition.name, 'update_voted', total_votes['total_votes'])

    return Response({'success': True}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def emoji_send(request, comp_name):
    input_text = request.data.get('text')
    
    competition = get_object_or_404(Competition, name=comp_name)
    # ensure the request user is a member of the competition
    get_object_or_404(Participant, user=request.user, competition=competition)
    # an emoji in unicode is 6 integers
    allowed_patt = r'(\d{4,6})'
    try:
        emoji = re.search(allowed_patt, f'{ord(input_text)}')
        emoji_text = chr(int(emoji.group(1)))
        if emoji_text:
            send_channel_message(competition.name, 'update_emoji', emoji_text)
    except TypeError:
        send_shame_message(competition.name, request.user.username)
        return Response({'detail': 'Nice try :)'}, status=status.HTTP_400_BAD_REQUEST)

    
    return Response({'success': True}, status=status.HTTP_200_OK)
