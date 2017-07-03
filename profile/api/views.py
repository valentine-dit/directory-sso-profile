from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_client import api_client


class ExternalSupplierAPIView(APIView):
    permission_classes = []
    authentication_classes = []
    http_method_names = ('get', )

    def get(self, request, format=None):
        if not request.sso_user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        response = api_client.buyer.retrieve_supplier(
            sso_session_id=self.request.sso_user.session_id
        )
        if response.ok:
            return Response(response.json())
        else:
            return Response(response.content, status=response.status_code)
