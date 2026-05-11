from rest_framework.throttling import AnonRateThrottle


class BookingCreateThrottle(AnonRateThrottle):
    """5 appointment creations per hour per IP."""
    scope = 'booking_create'


class SlotsThrottle(AnonRateThrottle):
    """60 slot lookups per hour per IP."""
    scope = 'slots'
