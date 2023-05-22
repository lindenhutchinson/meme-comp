from django.urls import re_path
from django.conf import settings
from . import consumers

websocket_urlpatterns = [
    re_path(settings.WEBSOCKET_SCHEME+r"/competitions/(?P<competition_name>\w+)/participant/(?P<participant_id>\d+)/$", consumers.CompetitionConsumer.as_asgi()),
]