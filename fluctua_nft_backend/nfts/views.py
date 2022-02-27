from rest_framework.generics import CreateAPIView, ListAPIView

from . import serializers, models


class PreSaveView(CreateAPIView):
    serializer_class = serializers.SpotifyPreSaveSerializer


class NftListView(ListAPIView):
    queryset = models.Nft.objects.all()
    serializer_class = serializers.NftSerializer
    filterset_fields = ["nft_type", "is_minted", "contract_id"]


class NftTypeListView(ListAPIView):
    queryset = models.NftType.objects.all()
    serializer_class = serializers.NftTypeSerializer
