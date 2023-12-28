from django.urls import include, path
from . import views, routing

urlpatterns = [
    path("", views.home, name="home"),
    path("lobby", views.lobby, name="lobby"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("competition/<str:comp_name>", views.competition, name="competition"),
    path(
        "competition/<str:comp_name>/results",
        views.competition_results,
        name="competition_results",
    ),
    path(
        "competition/<str:comp_name>/memes",
        views.competition_memes,
        name="competition_memes",
    ),
    path(
        "competition/<str:comp_name>/memes/<int:meme_id>",
        views.serve_file,
        name="serve_file",
    ),
    path("user/<int:id>", views.user_page, name="user"),
]

websocket_urlpatterns = routing.websocket_urlpatterns
urlpatterns += [path("ws/", include(websocket_urlpatterns))]
