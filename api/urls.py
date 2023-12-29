from django.urls import include, path
from . import views

urlpatterns = [
    path("competition/<str:comp_name>/upload", views.meme_upload, name="meme_upload"),
    path("meme/<int:meme_id>", views.meme_delete, name="meme_delete"),
    path("competition/<str:comp_name>/vote", views.meme_vote, name="meme_vote"),
    path(
        "competition/<str:comp_name>/start",
        views.start_competition,
        name="start_competition",
    ),
    path(
        "competition/<str:comp_name>/cancel",
        views.cancel_competition,
        name="cancel_competition",
    ),
    path(
        "competition/<str:comp_name>/advance",
        views.advance_competition,
        name="advance_competition",
    ),
]
