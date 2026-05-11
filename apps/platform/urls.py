from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PlatformLoginView,
    PlatformMeView,
    PlatformDashboardView,
    PlatformTenantViewSet,
    PlatformPlanViewSet,
    PlatformSubscriptionViewSet,
    PlatformDiscountViewSet,
    PlatformSettingsView,
    PublicPlanSettingsView,
)
from .paypal.views import (
    PayPalSyncPlansView,
    PayPalSubscribeView,
    PayPalReturnView,
    PayPalCancelView,
    PayPalWebhookView,
    PayPalSetProductIdsView,
)

app_name = 'platform'

router = DefaultRouter()
router.register(r'tenants', PlatformTenantViewSet, basename='platform-tenant')
router.register(r'plans', PlatformPlanViewSet, basename='platform-plan')
router.register(r'subscriptions', PlatformSubscriptionViewSet, basename='platform-subscription')
router.register(r'discounts', PlatformDiscountViewSet, basename='platform-discount')

urlpatterns = [
    path('auth/login/', PlatformLoginView.as_view(), name='login'),
    path('auth/me/', PlatformMeView.as_view(), name='me'),
    path('dashboard/', PlatformDashboardView.as_view(), name='dashboard'),
    path('settings/', PlatformSettingsView.as_view(), name='settings'),
    path('settings/public/', PublicPlanSettingsView.as_view(), name='settings-public'),

    # PayPal
    path('paypal/sync-plans/',         PayPalSyncPlansView.as_view(),  name='paypal-sync-plans'),
    path('paypal/set-product-ids/',    PayPalSetProductIdsView.as_view(), name='paypal-set-product-ids'),
    path('paypal/subscribe/<slug:slug>/', PayPalSubscribeView.as_view(), name='paypal-subscribe'),
    path('paypal/return/',             PayPalReturnView.as_view(),     name='paypal-return'),
    path('paypal/cancel/',             PayPalCancelView.as_view(),     name='paypal-cancel'),
    path('paypal/webhook/',            PayPalWebhookView.as_view(),    name='paypal-webhook'),

    path('', include(router.urls)),
]
