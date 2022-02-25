from rest_framework.generics import CreateAPIView

from . import serializers


class PreSaveView(CreateAPIView):
    serializer_class = serializers.SpotifyPreSaveSerializer
