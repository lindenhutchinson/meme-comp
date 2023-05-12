from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .utils import set_next_meme_for_competition
from .models import Meme, Competition, Vote, Participant
from .serializers import MemeSerializer

def send_channel_message(comp_name, consumer, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        comp_name, {"type": consumer, "data": data}
    )

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

    # Delete the meme
    meme.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])  # Use appropriate authentication classes
@permission_classes([IsAuthenticated])  # Use appropriate permission classes
def meme_upload(request, comp_name):
    print(request.data)
    serializer = MemeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        # Update total memes count
        competition = serializer.validated_data['competition']
        total_memes = competition.memes.count()
        send_channel_message(competition.name, 'update_uploaded', total_memes)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def start_competition(request, competition_id):
    # Process the competition start request
    try:
        competition = Competition.objects.get(id=competition_id)

        # Check if the request user is the owner of the competition
        if competition.owner == request.user:
            # Set the competition as started, set the current meme, etc.
            # Perform your desired logic here

            # Send channel update
            if competition.started:
                    return Response(
                    {"detail": "You have already started this competition"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
            competition = set_next_meme_for_competition(competition.id)
            
            send_channel_message(competition.name, 'next_meme', competition.current_meme.image)

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
def meme_vote(request,meme_id):
    if request.method == 'POST':
        score = request.data.get('score')
        participant = request.user.participant
        meme = get_object_or_404(Meme, id=meme_id)
        vote, created = Vote.objects.get_or_create(meme=meme, participant=participant)
        vote.score = score
        vote.save()
        total_votes = Vote.objects.filter(meme_id=meme_id).aggregate(total_votes=Count('id'))
        # Send channel update with "num_voted" command
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"competition_{meme.competition.id}",
            {
                'type': 'update_voted',
                'data': total_votes,
            }
        )

        return Response({'success': True}, status=status.HTTP_200_OK)