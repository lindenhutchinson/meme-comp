import pytest
from django.utils import timezone
from app.models import Competition, Participant, Meme, Vote, User
from faker import Faker

Faker.seed(1)

fakes = Faker()


@pytest.fixture
def fake():
    return Faker()


@pytest.fixture
def competition():
    user = User.objects.create(username=fakes.name())
    return Competition.objects.create(
        owner=user, theme="Test Theme", name=fakes.name(), started=True, finished=True
    )


@pytest.fixture
def participants(fake, competition):
    num_participants = 5
    participants = []
    for _ in range(num_participants):
        user = User.objects.create(username=fakes.name())
        participant = Participant.objects.create(
            name=fake.name(), competition=competition, user=user
        )
        participants.append(participant)
    return participants


@pytest.fixture
def memes(fake, competition, participants):
    memes = []
    for i, participant in enumerate(participants):

        for _ in range(i):
            meme = Meme.objects.create(
                image="test_image.jpg", competition=competition, participant=participant
            )
            memes.append(meme)
    return memes


@pytest.fixture
def votes(fake, memes, participants):
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
            )
            votes.append(vote)

    return votes


@pytest.mark.django_db
def test_competition_scores(competition, participants, memes, votes):
    # Check the final scores
    expected_avg_meme_score = calculate_expected_avg_meme_score(votes)
    assert competition.avg_meme_score == expected_avg_meme_score

    expected_highest_avg_score_given = calculate_expected_highest_avg_score_given(
        participants, votes
    )
    assert competition.highest_avg_score_given == expected_highest_avg_score_given

    expected_lowest_avg_score_given = calculate_expected_lowest_avg_score_given(
        participants, votes
    )
    assert competition.lowest_avg_score_given == expected_lowest_avg_score_given

    assert competition.highest_avg_score_received == {
        "participant": "Crystal Landry",
        "score": 3.8,
    }


def calculate_expected_avg_meme_score(votes):
    total_score = sum(vote.score for vote in votes)
    num_votes = len(votes)
    return round(total_score / num_votes, 2)


def calculate_expected_highest_avg_score_given(participants, votes):
    avg_scores = {}
    for participant in participants:
        scores = [vote.score for vote in votes if vote.participant == participant]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        avg_scores[participant.name] = avg_score
    highest_avg_score_given = max(avg_scores, key=avg_scores.get)
    return {
        "participant": highest_avg_score_given,
        "score": avg_scores[highest_avg_score_given],
    }


def calculate_expected_lowest_avg_score_given(participants, votes):
    avg_scores = {}
    for participant in participants:
        scores = [vote.score for vote in votes if vote.participant == participant]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        avg_scores[participant.name] = avg_score
    lowest_avg_score_given = min(avg_scores, key=avg_scores.get)
    return {
        "participant": lowest_avg_score_given,
        "score": avg_scores[lowest_avg_score_given],
    }


def calculate_expected_highest_avg_score_received(participants, votes):
    avg_scores = {}
    for participant in participants:
        scores = [vote.score for vote in votes if vote.meme.participant == participant]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        avg_scores[participant.name] = avg_score
    highest_avg_score_received = max(avg_scores, key=avg_scores.get)
    return {
        "participant": highest_avg_score_received,
        "score": avg_scores[highest_avg_score_received],
    }
