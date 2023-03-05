# Django Imports
from django.urls import path

# Local Imports
from . import views


app_name = 'callrouting'

urlpatterns = [
    path('', views.index, name='index'),
    path('handle', views.handle, name='handle'),
    path('volunteers/<int:user_group_id>/<str:day>/<int:hour>', views.volunteers, name='volunteers'),
    path('recording', views.recording, name='recording'),
    path('recordingcomplete', views.recordingcomplete, name='recordingcomplete'),
    path('transcription', views.transcription, name='transcription'),
]
