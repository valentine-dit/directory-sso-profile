from unittest.mock import patch

from profile.exops import helpers


@patch('requests.get')
def test_exporting_is_great_handles_auth(mock_get, settings):
    client = helpers.ExportingIsGreatClient()
    client.base_url = 'http://b.co'
    client.secret = 123
    username = settings.EXPORTING_OPPORTUNITIES_API_BASIC_AUTH_USERNAME
    password = settings.EXPORTING_OPPORTUNITIES_API_BASIC_AUTH_PASSWORD

    client.get_opportunities(2)

    mock_get.assert_called_once_with(
        'http://b.co/api/profile_dashboard',
        params={'user_id': 2, 'shared_secret': 123},
        auth=helpers.exporting_is_great_client.auth
    )
    assert helpers.exporting_is_great_client.auth.username == username
    assert helpers.exporting_is_great_client.auth.password == password
