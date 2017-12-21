from directory_healthcheck.views import BaseHealthCheckAPIView

from healthcheck.backends import APIProxyBackend, SigngleSignOnBackend


class APIProxyAPIView(BaseHealthCheckAPIView):
    def create_service_checker(self):
        return APIProxyBackend()


class SingleSignOnAPIView(BaseHealthCheckAPIView):
    def create_service_checker(self):
        return SigngleSignOnBackend()
