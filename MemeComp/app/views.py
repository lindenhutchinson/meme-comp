from django.shortcuts import render, redirect


from .utils import get_current_user, generate_random_string
from .forms import CompetitionForm, JoinCompetitionForm, LoginForm, UserForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from .models import Participant, Competition, User
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
            print(next_url)
            print('blah blah')
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
            print(next_url)
            print('blah blah')
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
                competition.name = generate_random_string(16)
                competition.save()
                participant, created = Participant.objects.get_or_create(name=user.username, user=user, competition=competition)
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
    _, created = Participant.objects.get_or_create(name=request.user.username, user=request.user, competition=comp)
    if created:
        messages.success(request, 'You have joined the competition!')
    context = {
        'competition': comp
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