from directory_healthcheck.views import BaseHealthCheckAPIView

from healthcheck.backends import SigngleSignOnBackend


class SingleSignOnAPIView(BaseHealthCheckAPIView):
    def create_service_checker(self):
        return SigngleSignOnBackend()
