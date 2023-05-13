import os
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count


from .utils import get_top_memes, set_next_meme_for_competition, send_channel_message
from .models import Meme, Competition, Vote, Participant, SeenMeme
from .serializers import MemeSerializer



@api_view(['DELETE'])
@authentication_classes([SessionAuthentication])  # Use appropriate authentication classes
@permission_classes([IsAuthenticated])  # Use appropriate permission classes
def meme_delete(request, meme_id):
    # Retrieve the meme object
    meme = get_object_or_404(Meme, id=meme_id)

    # Verify if the authenticated user has a participant associated with the meme
    if meme.participant.user != request.user:
        # User is not authorized to delete the meme
        return Response({"detail": "You are not authorized to delete this meme."}, status=status.HTTP_403_FORBIDDEN)

    meme.image.close()
    # Delete the file from the file system
    meme_image_path = os.path.join(settings.MEDIA_ROOT, meme.image.name)
    print(meme_image_path)
    try:
        os.remove(meme_image_path)
    except PermissionError:
        print('as expected')
        meme.image.close()

    try:
        if os.path.exists(meme_image_path):
            os.remove(meme_image_path)
        print('success')
    except PermissionError:
        print('you will not see this')

    # Delete the meme
    meme.delete()
    total_memes = meme.competition.memes.count()
    send_channel_message(meme.competition.name, 'update_uploaded', total_memes)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])  # Use appropriate authentication classes
@permission_classes([IsAuthenticated])  # Use appropriate permission classes
def meme_upload(request, comp_name):
    print(request.data)
    serializer = MemeSerializer(data=request.data)
    if serializer.is_valid():
        meme = serializer.save()

        # Update total memes count
        competition = serializer.validated_data['competition']
        total_memes = competition.memes.count()
        send_channel_message(competition.name, 'update_uploaded', total_memes)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def start_competition(request, comp_name):
    # Process the competition start request
    try:
        competition = Competition.objects.get(name=comp_name)

        # Check if the request user is the owner of the competition
        if competition.owner == request.user:
            if competition.started:
                    return Response(
                    {"detail": "You have already started this competition"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
            
            competition = set_next_meme_for_competition(competition.id)
            competition.started = True
            competition.save()
            send_channel_message(competition.name, 'next_meme', competition.current_meme.id)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "You are not authorized to start this competition."},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Competition.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def advance_competition(request, comp_name):  
 # Process the competition advance request
    try:
        competition = Competition.objects.get(name=comp_name)

        # Check if the request user is the owner of the competition
        if competition.owner == request.user:
            # Set the competition as started, set the current meme, etc.
            # Perform your desired logic here

            # Send channel update
            if not competition.started:
                    return Response(
                    {"detail": "You cannot advance a competition that hasnt started"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
            competition = set_next_meme_for_competition(competition.id)
            if competition.current_meme:
                send_channel_message(competition.name, 'next_meme', competition.current_meme.id)
            else:
                competition.finished = True
                competition.save()
                results = get_top_memes(competition.name, 3)
                send_channel_message(competition.name, 'competition_results', results)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "You are not authorized to advance this competition."},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Competition.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def cancel_competition(request, comp_name):
    # Process the competition cancel request
    try:
        competition = Competition.objects.get(name=comp_name)

        # Check if the request user is the owner of the competition
        if competition.owner == request.user:
            # Set the competition as started, set the current meme, etc.
            # Perform your desired logic here

            if not competition.started:
                    return Response(
                    {"detail": "This competition has not begun."},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
            competition.current_meme = None 
            competition.started = False
            competition.finished = False
            competition.save()  

            SeenMeme.objects.filter(competition=competition).delete()   
            comp_memes = competition.memes.all()
            votes = Vote.objects.filter(meme__in=comp_memes)
            print(votes)
            votes.delete()       

            send_channel_message(competition.name, 'cancel_competition', '')
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "You are not authorized to start this competition."},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Competition.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def meme_vote(request, comp_name):
    print(request.data)
    score = request.data.get('vote')
    print('this my score!', score)
    competition = Competition.objects.get(name=comp_name)
    participant = Participant.objects.get(user=request.user, competition=competition)
    meme = competition.current_meme
    try:
        vote = Vote.objects.get(meme=meme, participant=participant)
        vote.score = score
    except Vote.DoesNotExist:
        vote = Vote.objects.create(meme=meme, participant=participant, score=score)

    
    vote.save()
    print('got here')

    total_votes = Vote.objects.filter(meme_id=meme.id).aggregate(total_votes=Count('id'))
    total_participants = competition.participants.count()
    # Send channel update with "num_voted" command
    print(total_votes)
    send_channel_message(competition.name, 'update_voted', total_votes['total_votes'])

    return Response({'success': True}, status=status.HTTP_200_OK)