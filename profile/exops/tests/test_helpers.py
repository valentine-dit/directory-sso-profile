from unittest.mock import patch

from profile.exops import helpers


@patch('requests.get')
def test_exporting_is_great_handles_auth(mock_get, settings):
    client = helpers.ExportinIsGreatClient()
    client.base_url = 'http://b.co'
    client.secret = 123
    expected_username = settings.EXPORTING_IS_GREAT_API_BASIC_AUTH_USERNAME
    expected_password = settings.EXPORTING_IS_GREAT_API_BASIC_AUTH_PASSWORD
    client.get_opportunities(2)

    mock_get.assert_called_once_with(
        'http://b.co/api/profile_dashboard',
        params={'sso_user_id': 2, 'shared_secret': 123},
        auth=helpers.exporting_is_great_client.auth
    )
    assert helpers.exporting_is_great_client.auth.username == expected_username
    assert helpers.exporting_is_great_client.auth.password == expected_password
