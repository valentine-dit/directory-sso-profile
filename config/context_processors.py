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


def analytics(request):
    return {
        'analytics': {
            'GOOGLE_TAG_MANAGER_ID': settings.GOOGLE_TAG_MANAGER_ID,
            'GOOGLE_TAG_MANAGER_ENV': settings.GOOGLE_TAG_MANAGER_ENV,
            'UTM_COOKIE_DOMAIN': settings.UTM_COOKIE_DOMAIN,
        }
    }
