from directory_sso_api_client import sso_api_client


def create_user_profile(sso_session_id, data):
    response = sso_api_client.user.create_user_profile(
        sso_session_id=sso_session_id, data=data
    )
    response.raise_for_status()
    return response
