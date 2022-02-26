from rest_framework.generics import CreateAPIView, ListAPIView

from . import serializers, models


class PreSaveView(CreateAPIView):
    serializer_class = serializers.SpotifyPreSaveSerializer


class NftListView(ListAPIView):
    queryset = models.Nft.objects.all()
    serializer_class = serializers.NftSerializer


class NftTypeListView(ListAPIView):
    queryset = models.NftType.objects.all()
    serializer_class = serializers.NftTypeSerializer
