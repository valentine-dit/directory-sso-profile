from django.conf import settings


def feature_flags(request):
    return {
        'features': {
            'FEATURE_MULTI_USER_ACCOUNT_ENABLED': (
                settings.FEATURE_MULTI_USER_ACCOUNT_ENABLED
            ),
            'FEATURE_NEW_SHARED_HEADER_ENABLED': (
                settings.FEATURE_NEW_SHARED_HEADER_ENABLED
            )
        }
    }
