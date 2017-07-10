from requests import HTTPError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from profile.api.helpers import get_sso_id_from_request, get_supplier_profile


class ExternalSupplierAPIView(APIView):
    permission_classes = []
    authentication_classes = []
    http_method_names = ('get', )

    def get(self, request, format=None):
        sso_id = get_sso_id_from_request(request)
        if not sso_id:
            return Response('Unauthorized',
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            supplier = get_supplier_profile(sso_id=sso_id)
        except HTTPError as e:
            # HTTPError doesn't have the message attribute!
            return Response(str(e), status=e.response.status_code)
        return Response(supplier)
