from django.urls import path

from . import views

app_name = "nfts"
urlpatterns = [
    path("spotify-pre-saves/", view=views.PreSaveView.as_view(), name="spotify-pre-save"),
    path("", view=views.NftListView.as_view(), name="list-nfts"),
    path("types/", view=views.NftTypeListView.as_view(), name="list-nft-types"),
    path("claims/", view=views.NftClaimListView.as_view(), name="list-nft-claims"),
]
