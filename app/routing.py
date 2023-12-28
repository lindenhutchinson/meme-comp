from django.urls import re_path
from django.conf import settings
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"competitions/(?P<competition_name>\w+)/$",
        consumers.CompetitionConsumer.as_asgi(),
    ),
]
