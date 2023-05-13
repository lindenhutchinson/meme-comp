from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, HttpResponse
from .utils import get_current_user, generate_random_string, get_top_memes, send_channel_message
from .forms import CompetitionForm, JoinCompetitionForm, LoginForm, UserForm, UploadMemeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from .models import Participant, Competition, User, Meme
from django.views.decorators.http import require_POST

@require_POST
@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@require_POST
def login_view(request):
    form = LoginForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have been logged in!')
            next_url = request.POST.get('next')
            # if there is a next parameter, redirect the user to that URL
            if next_url:
                return redirect(next_url)
            return redirect('lobby')
        else:
            messages.error(request, 'Invalid login credentials.')
            
    else:
        # display form errors and non-field errors
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
            
    return redirect('home')

def home(request):
    if request.user.is_authenticated:
        return redirect('lobby')
       
    if request.method == 'POST':
        form = UserForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = User.objects.create(username=username)
            user.set_password(password)
            user.save()

            user = authenticate(request, username=username, password=password)
            login(request, user)
            messages.success(request, 'Successfully created your account!')
            
            next_url = request.POST.get('next')

            # if there is a next parameter, redirect the user to that URL
            if next_url:
                return redirect(next_url)

            return redirect('lobby')
        else:
            # display form errors and non-field errors
            for _, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UserForm()
        
    return render(request, 'home.html', {'form': form})

@login_required
def lobby(request):
    user = request.user
    competition_form = CompetitionForm()
    join_competition_form = JoinCompetitionForm()
    if request.method == 'POST':
        if 'create' in request.POST:
            competition_form = CompetitionForm(request.POST)
            if competition_form.is_valid():
                competition = competition_form.save(commit=False)
                competition.owner = request.user
                competition.name = generate_random_string(8)
                competition.save()
                _, created = Participant.objects.get_or_create(name=user.username, user=user, competition=competition)
                if created:
                    messages.success(request, 'Competition created successfully!')
                    return redirect('competition', comp_name=competition.name)

        elif 'join' in request.POST:
            join_competition_form = JoinCompetitionForm(request.POST)
            if join_competition_form.is_valid():
                competition_name = join_competition_form.cleaned_data['name']
                try:
                    competition = Competition.objects.get(name=competition_name)
                except Competition.DoesNotExist:
                    messages.error(request, 'Invalid competition ID')
                else:
                    request.session['competition_id'] = competition.id
                    _, created = Participant.objects.get_or_create(name=user.username, user=user, competition=competition)
                    if created:
                        messages.success(request, 'You have joined the competition!')
                        total_participants = competition.participants.count()
                        send_channel_message(competition.name, 'update_joined', total_participants)
                    else:
                        messages.warning(request, 'You have already joined this competition.')
                        
                    return redirect('competition', comp_name=competition.name)

    return render(request, 'lobby.html', {
        'competition_form': competition_form,
        'join_competition_form': join_competition_form,
    })


@login_required
def competition(request, comp_name):
    comp = Competition.objects.get(name=comp_name)
    participant, created = Participant.objects.get_or_create(name=request.user.username, user=request.user, competition=comp)
    if created:
        messages.success(request, 'You have joined the competition!')
    
    request.session['competition_id'] = comp.id
    request.session['participant_id'] = participant.id
    if comp.started and not comp.current_meme:
        top_memes = get_top_memes(comp.name, 3)
    else:
        top_memes = []
    context = {
        'participant': participant,
        'competition': comp,
        'top_memes': top_memes
    }
    return render(request, 'competition.html', context)


@login_required
def joined_competitions(request):
    participant_list = Participant.objects.filter(user=request.user)
    competitions = []
    for participant in participant_list:
        competitions.append({
            'name': participant.competition.name,
            'theme': participant.competition.theme,
        })

    context = {
        'competitions': competitions
    }
    return render(request, 'joined_competitions.html', context)

# @login_required
# @require_POST
# def upload_meme(request):
#     participant_id = request.session.get('participant_id')
#     competition_id = request.session.get('competition_id')
    
#     if not (participant_id and competition_id):
#         messages.error('Something went wrong, try again')
#         return redirect('lobby')
        
#     try:
#         participant = Participant.objects.get(id=participant_id)
#         competition = Competition.objects.get(id=competition_id)
        
#         form = UploadMemeForm(request.POST, request.FILES)
#         if form.is_valid():
#             image = form.cleaned_data['image']
            
#             if image.size > 4 * 1024 * 1024:
#                 messages.warning('Your files are too powerful!')
                
#             else:
#                 meme = Meme()
#                 meme.image = image
#                 meme.participant = participant
#                 meme.competition = competition
#                 meme.save()
                
#             channel_layer = get_channel_layer()
            
#             async_to_sync(channel_layer.group_send)(competition.name, {"type":"meme_uploaded", "data":competition.num_memes})
            
#         return redirect('competition', comp_name=competition.name)
                     
#     except (Participant.DoesNotExist, Competition.DoesNotExist):
#         messages.error('Some went wrong, try again')
#         return redirect('lobby')
        
#     return redirect('lobby')
        

def serve_file(request, comp_name, meme_id):
    # Check if the user has joined the competition
    competition = get_object_or_404(Competition, name=comp_name)
    if not competition.participants.filter(user=request.user).exists():
        return HttpResponse.HttpResponseForbidden()

    # Get the file object
    meme = get_object_or_404(Meme, id=meme_id, competition=competition)
    file_data = ContentFile(meme.image.read(), name=meme.image.name)
    file_data.content_type = 'image/*'
    # Serve the file
    response = HttpResponse(file_data, content_type=file_data.content_type)
    response['Content-Disposition'] = f'attachment; filename="{meme.image.name}"'
    return response
 
# @login_required  
# def delete_meme(request, meme_id):
#     # Get the meme object
#     meme = get_object_or_404(Meme, id=meme_id)
#     # Verify if the authenticated user has a participant associated with the meme
#     if meme.participant.user != request.user:
#         # User is not authorized to delete the meme
#         messages.error(request, "You are not authorized to delete this meme.")
#         return redirect('competition', comp_name=meme.competition.name)
    
#     competition = meme.competition
#     # Delete the meme
#     meme.delete()

#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(competition.name, {"type":"meme_uploaded", "data":competition.num_memes})
#     messages.success(request, "Meme deleted successfully.")
#     return redirect('competition', comp_name=meme.competition.name)
    