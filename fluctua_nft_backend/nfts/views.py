from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework import status
from rest_framework.response import Response

from . import serializers, models


class PreSaveView(CreateAPIView):
    serializer_class = serializers.SpotifyPreSaveSerializer


class NftListView(ListAPIView):
    queryset = models.Nft.objects.all()
    serializer_class = serializers.NftSerializer
    filterset_fields = {
        "nft_type": ["exact"],
        "is_minted": ["exact"],
        "contract_id": ["exact", "in"],
    }


class NftTypeListView(ListAPIView):
    queryset = models.NftType.objects.all()
    serializer_class = serializers.NftTypeSerializer


class NftClaimListView(ListAPIView):
    queryset = models.NftClaim.objects.all()
    serializer_class = serializers.NftClaimSerializer
    filterset_fields = ["user__email", "nft__contract_id", "nft__nft_type"]


class NftContentView(GenericAPIView):
    serializer_class = serializers.NftContentSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                status=status.HTTP_422_UNPROCESSABLE_ENTITY, data=serializer.errors
            )
        else:
            nft_content = models.NftContent.objects.filter(nft_type__nft__contract_id = serializer.data.get("nft"))
            if not nft_content.count():
                return Response(status=status.HTTP_404_NOT_FOUND)
            else:
                response_payload = serializers.NftContentModelSerializer(nft_content, many=True).data
                return Response(status=status.HTTP_200_OK, data=response_payload)

