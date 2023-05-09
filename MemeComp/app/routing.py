from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/competitions/(?P<competition_name>\w+)/$", consumers.CompetitionConsumer.as_asgi()),
]