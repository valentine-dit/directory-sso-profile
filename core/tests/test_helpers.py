from unittest import mock

from core import helpers

from core.tests.helpers import create_response


@mock.patch.object(helpers.sso_api_client.user, 'create_user_profile')
def test_create_user_profile(mock_create_user_profile):
    data = {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'job_title': 'Director',
        'mobile_phone_number': '08888888888',
    }
    mock_create_user_profile.return_value = create_response(201, data)
    helpers.create_user_profile(
        sso_session_id=1,
        data=data
    )
    assert mock_create_user_profile.call_count == 1
    assert mock_create_user_profile.call_args == mock.call(
        sso_session_id=1, data=data
    )
