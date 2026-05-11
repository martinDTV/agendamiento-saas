from rest_framework.routers import DefaultRouter

from .views import RoomViewSet, MeetingViewSet

app_name = 'meetings'

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'meetings', MeetingViewSet, basename='meeting')

urlpatterns = router.urls
