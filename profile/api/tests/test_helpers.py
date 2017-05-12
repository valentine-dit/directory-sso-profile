from unittest.mock import Mock, patch

from profile.api.helpers import get_sso_id_from_request


@patch('profile.api.helpers.requests')
def test_get_sso_id_from_request(mock_requests, settings):
    settings.SSO_API_OAUTH2_BASE_URL = 'http://test.com/'
    mock_request = Mock(META={'Authorization': 'Bearer 123'})
    mock_requests.get.return_value.json.return_value = {'id': 123}

    token = get_sso_id_from_request(request=mock_request)

    assert token == 123
    assert mock_requests.get.called_once_with(
        'http://test.com/user-profile/v1/',
        headers={'Authorization': 'Bearer 123'}
    )
