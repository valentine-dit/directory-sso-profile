import directory_sso_api_client.models

from django.db import models


class SSOUser(directory_sso_api_client.models.SSOUser):
    has_user_profile = models.BooleanField()
