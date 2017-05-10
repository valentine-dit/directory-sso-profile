from requests import HTTPError
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import get_supplier_profile


class ExternalSupplierAPIView(APIView):
    permission_classes = []
    authentication_classes = []
    http_method_names = ('get', )

    def get(self, request, sso_id, format=None):
        try:
            supplier = get_supplier_profile(sso_id=sso_id)
        except HTTPError:
            pass
        return Response(supplier)
