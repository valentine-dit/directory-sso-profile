from directory_sso_api_client import backends


class SSOUserBackend(backends.SSOUserBackend):
    def user_kwargs(self, session_id, parsed):
        user_profile = parsed.get('user_profile') or {}
        return {
            'has_user_profile': bool(user_profile),
            'first_name': user_profile.get('first_name'),
            'last_name': user_profile.get('last_name'),
            **super().user_kwargs(session_id=session_id, parsed=parsed)
        }
