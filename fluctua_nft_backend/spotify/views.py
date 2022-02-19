from urllib.parse import urlencode

from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


class InfoView(APIView):
    """
    Returns information and configuration of the service
    """

    renderer_classes = (JSONRenderer,)

    # @method_decorator(cache_page(60 * 60))  # 1 hour
    def get(self, request, format=None):
        query = {
            "scope": "user-library-modify user-read-email",
            "response_type": "code",
            "client_id": "92fec7cd91604f69a1d9a2327d7c515c"
        }
        content = {
            "authorizationUrl": "https://accounts.spotify.com/en/authorize?" + urlencode(query)
        }
        return Response(content)
