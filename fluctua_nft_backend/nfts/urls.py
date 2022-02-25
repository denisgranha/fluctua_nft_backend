from django.urls import path

from . import views

app_name = "nfts"
urlpatterns = [
    path("spotify-pre-save/", view=views.PreSaveView.as_view(), name="spotify-pre-save"),
]
