from django.urls import include, path
from . import views, routing, api
urlpatterns = [
    path('', views.home, name='home'),
    path('lobby', views.lobby, name='lobby'),
    path('competition/<str:comp_name>', views.competition, name='competition'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view,name='logout'),
    path('competition/<str:comp_name>/memes/<int:meme_id>', views.serve_file, name='serve_file'),
    # path('delete_meme/<int:meme_id>', views.delete_meme, name='delete_meme'),
    # path('create/', views.create_competition, name='create_competition'),
    # path('competition/<str:competition_id>/', views.competition_detail, name='competition_detail'),
    # path('competition/<str:competition_id>/join/', views.join_competition, name='join_competition'),
    # path('competition/<str:competition_id>/submit/', views.submit_meme, name='submit_meme'),
    # path('competition/<str:competition_id>/start/', views.start_competition, name='start_competition'),
    # path('competition/<str:competition_id>/vote/', views.vote, name='vote'),
    # path('competition/<str:competition_id>/results/', views.results, name='results'),
    
    path('api/competition/<str:comp_name>/upload', api.meme_upload, name='meme_upload'),
    path('api/meme/<int:meme_id>', api.meme_delete, name='meme_delete'),
    path('api/competition/<str:comp_name>/vote', api.meme_vote, name='meme_vote'),
    path('api/competition/<str:comp_name>/start', api.start_competition, name="start_competition"),
    path('api/competition/<str:comp_name>/cancel', api.cancel_competition, name="cancel_competition"),
    path('api/competition/<str:comp_name>/advance', api.advance_competition, name="advance_competition")

]

websocket_urlpatterns = routing.websocket_urlpatterns
urlpatterns += [path('ws/', include(websocket_urlpatterns))]
