from django.urls import path

from . import views

app_name = "spotify"
urlpatterns = [
    path("info/", view=views.InfoView.as_view(), name="detail"),
]
