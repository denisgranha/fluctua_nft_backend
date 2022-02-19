from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SpotifyConfig(AppConfig):
    name = "fluctua_nft_backend.spotify"
    verbose_name = _("Spotify")
