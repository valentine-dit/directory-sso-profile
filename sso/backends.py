from directory_sso_api_client import backends


class SSOUserBackend(backends.SSOUserBackend):
    def user_kwargs(self, session_id, parsed):
        return {
            'has_user_profile': parsed['has_user_profile'],
            **super().user_kwargs(session_id=session_id, parsed=parsed)
        }
