from rest_framework import authentication, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_client import api_client


class ExternalSupplierAPIView(APIView):
    permission_classes = []
    authentication_classes = []
    http_method_names = ('get', )

    def get(self, request, format=None):
        auth = authentication.get_authorization_header(request).split()
        if not auth or len(auth) == 1 or auth[0].decode() != 'Bearer':
            return Response(
                'Unauthorized', status=status.HTTP_401_UNAUTHORIZED
            )
        response = api_client.buyer.retrieve_supplier(auth[1])
        if response.ok:
            return Response(response.json())
        else:
            return Response(
                response.content, status=response.status_code.value
            )
