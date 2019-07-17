from unittest.mock import Mock

from django.urls import reverse
from django.views.generic import TemplateView

from profile.fab import state_requirements


class BaseTestView(TemplateView):
    template_name = 'company-profile-detail.html'


class CompanyTestView(BaseTestView):
    company = {'number': 123456}


class NoCompanyTestView(BaseTestView):
    company = {}


class VerifiedCompanyTestView(BaseTestView):
    company = {'is_verified': True}


class UnverifiedCompanyTestView(BaseTestView):
    company = {'is_verified': False}


class VerificationLetterSentTestView(BaseTestView):
    company = {'is_verification_letter_sent': True}


def create_view_for_rule(rule_class, ViewClass=BaseTestView):
    class TestView(
        state_requirements.UserStateRequirementHandlerMixin, ViewClass
    ):
        required_user_states = [rule_class]
    return TestView.as_view()


def test_redirect_rule_handler_mixin_provides_context():
    pass


def test_redirect_rule_handler_mixin_redirect_required(rf):
    class RedirectRequired(state_requirements.RedirectUserStateRule):
        redirect_url = '/some/url'

        def is_user_in_required_state(self):
            return False

    view = create_view_for_rule(RedirectRequired, BaseTestView)
    response = view(rf.get('/'))

    assert response.status_code == 302
    assert response.url == '/some/url'


def test_redirect_rule_handler_mixin_redirect_not_required(rf):
    class RedirectNotRequired(state_requirements.RedirectUserStateRule):
        redirect_url = '/some/url'

        def is_user_in_required_state(self):
            return True

    view = create_view_for_rule(RedirectNotRequired)
    response = view(rf.get('/'))

    assert response.status_code == 200


def test_company_required_rule_has_company(rf):
    view = create_view_for_rule(
        state_requirements.HasCompany, CompanyTestView
    )
    response = view(rf.get('/'))

    assert response.status_code == 200


def test_company_required_rule_no_company(rf):
    view = create_view_for_rule(
        state_requirements.HasCompany, NoCompanyTestView
    )
    response = view(rf.get('/'))

    assert response.status_code == 302
    assert response.url == reverse('index')


def test_no_company_required_rule_has_company(rf):
    view = create_view_for_rule(
        state_requirements.NoCompany, CompanyTestView
    )
    response = view(rf.get('/'))

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')


def test_no_company_required_rule_no_company(rf):
    view = create_view_for_rule(
        state_requirements.NoCompany, NoCompanyTestView
    )
    response = view(rf.get('/'))

    assert response.status_code == 200
