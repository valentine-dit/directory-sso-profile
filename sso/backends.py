from django.contrib import auth

from directory_sso_api_client import backends 


class SSOUserBackend(backends.SSOUserBackend):
    def build_user(self, session_id, parsed):
        SSOUser = auth.get_user_model()
        return SSOUser(
            id=parsed['id'],
            session_id=session_id,
            hashed_uuid=parsed['hashed_uuid'],
            email=parsed['email'],
            has_user_profile=parsed['has_user_profile'],
        )
