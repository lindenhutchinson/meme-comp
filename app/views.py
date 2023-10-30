from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, HttpResponse
from .utils import convert_to_localtime, generate_random_string, get_top_memes, send_channel_message
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
from django.db.models import Count
from datetime import datetime
from django.db.models import Q, F, Avg
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
            # messages.success(request, 'You have been logged in!')
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
            # messages.success(request, 'Successfully created your account!')
            
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
                    participant, created = Participant.objects.get_or_create(name=user.username, user=user, competition=competition)
                    if created:
                        data = {
                            'num_participants':competition.participants.count(),
                            'name':participant.name,
                            'id':participant.id,
                            'user_id':user.id,
                        }
                        send_channel_message(competition.name, 'user_joined', data)
                    else:
                        messages.warning(request, 'You have already joined this competition.')
                        
                    return redirect('competition', comp_name=competition.name)
    
    participant_list = Participant.objects.filter(user=request.user)
    competitions = []
    for participant in participant_list:
        competitions.append({
            'name': participant.competition.name,
            'theme': participant.competition.theme,
            'created_at':participant.competition.created_at
        })
        
    sorted_comps = sorted(competitions, key=lambda x : datetime.strftime(x['created_at'], '%Y/%m/%d %H:%M:%S'), reverse=True)
    

    return render(request, 'lobby.html', {
        'competitions': sorted_comps,
        'competition_form': competition_form,
        'join_competition_form': join_competition_form,
    })

@login_required
def competition(request, comp_name):
    comp = get_object_or_404(Competition, name=comp_name)
    participant, created = Participant.objects.get_or_create(name=request.user.username, user=request.user, competition=comp)
    if created:
        data = {
            'num_participants':comp.participants.count(),
            'name':participant.name,
            'id':participant.id,
            'user_id':request.user.id
        }
        send_channel_message(comp.name, 'user_joined', data)
    
    request.session['competition_id'] = comp.id
    request.session['participant_id'] = participant.id

    context = {
        'participant': participant,
        'competition': comp,
        'websocket_scheme': settings.WEBSOCKET_SCHEME
    }
    return render(request, 'competition.html', context)

@login_required
def competition_results(request, comp_name):
    comp = get_object_or_404(Competition, name=comp_name)
    participant = get_object_or_404(Participant, user=request.user, competition=comp)
    participants = list(comp.participants.annotate(meme_count=Count('memes')).order_by('-meme_count'))
    participants.sort(key=lambda p: p.top_meme.avg_score if p.top_meme else 0, reverse=True)
    participants.remove(participant)
    participants.insert(0, participant)
    context = {
        'competition':comp,
        'participants':participants,
        'participant':participant
    }
    return render(request, 'results.html', context)

@login_required
def serve_file(request, comp_name, meme_id):
    # Check if the user has joined the competition
    competition = get_object_or_404(Competition, name=comp_name)
    if not competition.participants.filter(user=request.user).exists():
        return HttpResponse("Access Forbidden", status=403)

    # Get the file object
    meme = get_object_or_404(Meme, id=meme_id, competition=competition)
    
    # only the uploader of the meme can access it before the competition has started
    if not competition.started and meme.participant.user != request.user:
        return HttpResponse("Access Forbidden", status=403)
    try:
        file_data = ContentFile(meme.image.read(), name=meme.image.name)
        file_data.content_type = 'image/*'
        # Serve the file
        response = HttpResponse(file_data, content_type=file_data.content_type)
        response['Content-Disposition'] = f'attachment; filename="{meme.image.name}"'
        response['Cache-Control'] = 'public, max-age=3600'
        return response
    except FileNotFoundError:
        return HttpResponse("Not Found", status=404)


@login_required
def user_page(request, id):
    user = get_object_or_404(User, id=id)

    # only allow users to view the users they share a competition with
    if not user.shares_comp_with(request.user) and not user == request.user:
        return HttpResponse("Access Forbidden", status=403)

    themes = user.participants.filter(competition__finished=True).values_list('competition__theme', flat=True).distinct()

    # Start with the base queryset for the user's meme library
    meme_library = Meme.objects.filter(user=user, competition__finished=True)

    # Calculate the average score for each meme and annotate it to the queryset
    meme_library = meme_library.annotate(average_score=Avg('votes__score')).order_by('-average_score')

    # Prefetch related fields to reduce database queries
    meme_library = meme_library.select_related('competition', 'participant')

    context = {
        'view_user': user,
        'meme_library': meme_library,
        'themes':themes
    }
    return render(request, 'user.html', context)


@login_required
def competition_memes(request, comp_name):
    comp = get_object_or_404(Competition, name=comp_name)
    # only users that have joined the competition are allowed to view the memes
    if not comp.participants.filter(user=request.user).exists():
        return HttpResponse("Access Forbidden", status=403)
    
    if not comp.finished:
        return HttpResponse("You're not allowed to view the memes of an unfinished competition", status=403)
    
    return render(request, 'comp_memes.html', {'competition': comp})