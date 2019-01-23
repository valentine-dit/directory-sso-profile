from directory_ch_client.client import ch_search_api_client
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core import serializers


class CompaniesHouseSearchApiView(GenericAPIView):
    serializer_class = serializers.CompaniesHouseSearchSerializer
    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        response = ch_search_api_client.company.search_companies(
            query=serializer.validated_data['term']
        )
        response.raise_for_status()
        return Response(response.json()['items'])
