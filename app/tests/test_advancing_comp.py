import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from faker import Faker
from app.models import (
    User,
    Competition,
    Participant,
    Meme,
    SeenMeme,
    Vote,
)

Faker.seed(1)

fake = Faker()




from app.utils import (
    run_advance_competition,
    set_next_meme_for_competition,
)


@pytest.fixture
def competition():
    user = User.objects.create(username=fake.name())
    return Competition.objects.create(
        owner=user, theme="Test Theme", 
    )

@pytest.fixture
def participants(competition, num_participants=5):
    participants = []
    for _ in range(num_participants):
        user = User.objects.create(username=fake.name())
        participant = Participant.objects.create(
            name=fake.name(), competition=competition, user=user
        )
        participants.append(participant)
    return participants

@pytest.fixture
def memes(competition, participants):
    memes = []
    for i, participant in enumerate(participants):

        for _ in range(i):
            meme = Meme.objects.create(
                image="test_image.jpg", competition=competition, participant=participant, user=participant.user
            )
            memes.append(meme)
    return memes


@pytest.fixture
def votes(memes, participants):
    votes = []

    for participant in participants:
        for meme in memes:
            score = fake.random_int(
                min=1, max=5
            )  # Generate a random score between 1 and 5
            vote = Vote.objects.create(
                meme=meme,
                participant=participant,
                competition=meme.competition,
                score=score,
                started_at=meme.competition.created_at,
                user=participant.user
            )
            votes.append(vote)

    return votes

@pytest.mark.django_db
def test_set_next_meme_for_competition(competition, memes, participants):
    # Set up seen memes for the competition
    for meme in memes[:len(memes)//2]:
        SeenMeme.objects.create(meme=meme, competition=competition)

    # Set the round_started_at to a past date to simulate an ongoing competition
    round_started_at = competition.round_started_at = datetime.now(tz=timezone.get_current_timezone()) - timedelta(days=1)
    competition.save()

    # Call the function
    updated_competition = set_next_meme_for_competition(competition)

    # Assertions
    assert updated_competition.current_meme is not None
    assert updated_competition.round_started_at > round_started_at
    assert not updated_competition.finished

@pytest.mark.django_db
def test_run_advance_competition_not_started(competition, participants, memes, votes):
    # Set up competition data
    competition.current_meme = memes[0]
    competition.save()

    # Call the function
    run_advance_competition(competition)

    # Assertions for competition state after running the function
    competition.refresh_from_db()
    assert competition.current_meme is not None or competition.finished
    if competition.finished:
        assert competition.winning_meme is not None

@pytest.mark.django_db
def test_run_advance_competition_started_not_finished(competition, participants, memes, votes):
    # Set up competition data
    competition.current_meme = memes[0]
    competition.state = Competition.CompState.STARTED
    competition.save()

    # Call the function
    run_advance_competition(competition)

    # Assertions for competition state after running the function
    competition.refresh_from_db()
    assert competition.current_meme is not None or competition.finished
    if competition.finished:
        assert competition.winning_meme is not None

@pytest.mark.django_db
def test_run_advance_competition_finished(competition, participants, memes, votes):
    # Set up competition data
    competition.current_meme = memes[0]
    
    # set all memes as seen for this competition
    for meme in memes:
        SeenMeme.objects.create(meme=meme, competition=competition)
    
    competition.state = Competition.CompState.STARTED
    competition.save()

    # Call the function
    run_advance_competition(competition)

    # Assertions for competition state after running the function
    competition.refresh_from_db()
    assert not competition.current_meme and competition.finished
    assert competition.winning_meme is not None
    assert competition.finished
