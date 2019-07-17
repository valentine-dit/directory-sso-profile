import abc

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse_lazy


class UserStateRule(abc.ABC):

    def __init__(self, context):
        self.context = context

    @abc.abstractmethod
    def handle_invalid_state(self):
        """
        Return a HttpResponse due to the user not being in the required state.

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def is_user_in_required_state(self):
        raise NotImplementedError()


class RedirectUserStateRule(UserStateRule):

    @property
    def redirect_url(self):
        """ The url to redirect to"""
        raise NotImplementedError()

    def handle_invalid_state(self):
        return redirect(self.redirect_url)


class UserStateRequirementHandlerMixin:

    required_user_states = []

    def dispatch(self, *args, **kwargs):
        for rule_class in self.required_user_states:
            rule = rule_class(context={'request': self.request, 'view': self})
            if not rule.is_user_in_required_state():
                return rule.handle_invalid_state()
        return super().dispatch(*args, **kwargs)


class HasCompany(RedirectUserStateRule):

    redirect_url = reverse_lazy('index')

    def is_user_in_required_state(self):
        return bool(self.context['view'].company)


class NoCompany(RedirectUserStateRule):

    redirect_url = reverse_lazy('find-a-buyer')

    def is_user_in_required_state(self):
        return not self.context['view'].company
