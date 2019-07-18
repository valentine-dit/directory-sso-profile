import directory_sso_api_client.models

from django.db import models
from django.utils.functional import cached_property

from profile.fab import helpers


class SSOUser(directory_sso_api_client.models.SSOUser):
    has_user_profile = models.BooleanField()

    @cached_property
    def company(self):
        company = helpers.get_company_profile(self.session_id)
        if company:
            return helpers.CompanyParser(company)
