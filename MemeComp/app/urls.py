from django.urls import include, path
from . import views, routing
urlpatterns = [
    path('', views.home, name='home'),
    path('lobby', views.lobby, name='lobby'),
    path('competition/<str:comp_name>', views.competition, name='competition'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view,name='logout'),
    path('competitions', views.joined_competitions, name='joined_competitions')
    # path('create/', views.create_competition, name='create_competition'),
    # path('competition/<str:competition_id>/', views.competition_detail, name='competition_detail'),
    # path('competition/<str:competition_id>/join/', views.join_competition, name='join_competition'),
    # path('competition/<str:competition_id>/submit/', views.submit_meme, name='submit_meme'),
    # path('competition/<str:competition_id>/start/', views.start_competition, name='start_competition'),
    # path('competition/<str:competition_id>/vote/', views.vote, name='vote'),
    # path('competition/<str:competition_id>/results/', views.results, name='results'),
]

websocket_urlpatterns = routing.websocket_urlpatterns
urlpatterns += [path('ws/', include(websocket_urlpatterns))]
