from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NftsConfig(AppConfig):
    name = "fluctua_nft_backend.nfts"
    verbose_name = _("NFTs")
