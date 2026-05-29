from .settings import *  # noqa: F401, F403

# Disable throttling in tests: keep scopes defined but allow unlimited requests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # type: ignore[index]  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {  # type: ignore[index]  # noqa: F405
    'anon': '10000/hour',
    'user': '10000/hour',
    'booking_create': '10000/hour',
    'slots': '10000/hour',
    'postal_code': '10000/hour',
    'geocode': '10000/hour',
    'anonymous_review': '10000/hour',
}
