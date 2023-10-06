from django.urls import include, path
from . import views, routing, api
urlpatterns = [
    path('', views.home, name='home'),
    path('lobby', views.lobby, name='lobby'),
    path('competition/<str:comp_name>', views.competition, name='competition'),
    path('competition/<str:comp_name>/results', views.competition_results, name='competition_results'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view,name='logout'),
    path('competition/<str:comp_name>/memes/<int:meme_id>', views.serve_file, name='serve_file'),
    path('user/<int:id>', views.user_page, name='user'),
    #######################################################################
    path('api/competition/<str:comp_name>/upload', api.meme_upload, name='meme_upload'),
    path('api/meme/<int:meme_id>', api.meme_delete, name='meme_delete'),
    path('api/competition/<str:comp_name>/vote', api.meme_vote, name='meme_vote'),
    path('api/competition/<str:comp_name>/start', api.start_competition, name="start_competition"),
    path('api/competition/<str:comp_name>/cancel', api.cancel_competition, name="cancel_competition"),
    path('api/competition/<str:comp_name>/advance', api.advance_competition, name="advance_competition"),
    path('api/participant/<int:part_id>/ready', api.readyup_participant, name="readyup_participant"),
]

websocket_urlpatterns = routing.websocket_urlpatterns
urlpatterns += [path('ws/', include(websocket_urlpatterns))]
