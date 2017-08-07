from django.http import HttpResponse

from config import middleware


def test_no_cache_middlware_installed(settings):
    assert 'config.middleware.NoCacheMiddlware' in settings.MIDDLEWARE_CLASSES


def test_no_cache_middlware(rf):
    request = rf.get('/')
    response = HttpResponse()

    output = middleware.NoCacheMiddlware().process_response(request, response)

    assert output == response
    assert output['Cache-Control'] == 'no-store, no-cache'
