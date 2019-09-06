from directory_constants import user_roles
import directory_sso_api_client.models

from django.db import models
from django.utils.functional import cached_property

from profile.fab import helpers


class SSOUser(directory_sso_api_client.models.SSOUser):
    has_user_profile = models.BooleanField()
    job_title = models.CharField(max_length=123)
    mobile_phone_number = models.CharField(max_length=128)

    @cached_property
    def company(self):
        company = helpers.get_company_profile(self.session_id)
        if company:
            return helpers.CompanyParser(company)

    @cached_property
    def supplier(self):
        return helpers.get_supplier_profile(self.session_id)

    @property
    def is_company_admin(self):
        return self.supplier['role'] == user_roles.ADMIN

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
