from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework import status
from rest_framework.response import Response
from gnosis.eth.django.filters import EthereumAddressFilter
from gnosis.eth.django.models import EthereumAddressV2Field
import django_filters

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


class NftClaimFilter(django_filters.FilterSet):
    class Meta:
        model = models.NftClaim
        fields = {
            "user__ethereum_address": ["exact"],
            "nft__contract_id": ["exact"],
            "nft__nft_type": ["exact"],
        }
        filter_overrides = {
            EthereumAddressV2Field: {"filter_class": EthereumAddressFilter},
        }


class NftClaimListView(ListAPIView):
    queryset = models.NftClaim.objects.all()
    serializer_class = serializers.NftClaimSerializer
    filterset_class = NftClaimFilter


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

