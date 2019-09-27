from directory_sso_api_client import sso_api_client
from directory_api_client.client import api_client


def create_user_profile(sso_session_id, data):
    profile_response = sso_api_client.user.create_user_profile(
        sso_session_id=sso_session_id, data=data
    )
    profile_response.raise_for_status()
    # Call made to Supplier to keep name in Sync
    # To be removed once we remove from supplier model
    response = update_supplier_profile_name(sso_session_id, data)
    response.raise_for_status()
    return profile_response


def update_user_profile(sso_session_id, data):
    profile_response = sso_api_client.user.update_user_profile(
        sso_session_id=sso_session_id, data=data
    )
    profile_response.raise_for_status()
    # Call made to Supplier to keep name in Sync
    # To be removed once we remove from supplier model
    response = update_supplier_profile_name(sso_session_id, data)
    response.raise_for_status()
    return profile_response


def update_supplier_profile_name(sso_session_id, data):
    response = api_client.supplier.profile_update(
        sso_session_id=sso_session_id,
        data={'name': extract_full_name(data)}
    )
    response.raise_for_status()
    return response


def extract_full_name(data):
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    return f'{first_name} {last_name}'
