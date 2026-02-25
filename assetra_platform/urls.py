from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from assetra.views import (
    AssetCategoryViewSet,
    AssetViewSet,
    BarcodeValidationView,
    BarcodeBatchViewSet,
    DeviceProfileViewSet,
    HealthCheckView,
    IndustryPresetViewSet,
    IntegrationConnectorViewSet,
    InventorySessionViewSet,
    LiveDataView,
    LivenessProbeView,
    LookupView,
    LocationViewSet,
    MetricsView,
    NoCodeFormDefinitionViewSet,
    ScanEventViewSet,
    SyncView,
    TenantViewSet,
    WebhookInboundView,
    WebhookEndpointViewSet,
    WorkflowDefinitionViewSet,
    WorkflowRunViewSet,
)

router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenant")
router.register("locations", LocationViewSet, basename="location")
router.register("asset-categories", AssetCategoryViewSet, basename="asset-category")
router.register("assets", AssetViewSet, basename="asset")
router.register("scan-events", ScanEventViewSet, basename="scan-event")
router.register("inventory-sessions", InventorySessionViewSet, basename="inventory-session")
router.register("workflow-definitions", WorkflowDefinitionViewSet, basename="workflow-definition")
router.register("workflow-runs", WorkflowRunViewSet, basename="workflow-run")
router.register("form-definitions", NoCodeFormDefinitionViewSet, basename="form-definition")
router.register("barcode-batches", BarcodeBatchViewSet, basename="barcode-batch")
router.register("webhooks", WebhookEndpointViewSet, basename="webhook")
router.register("integrations", IntegrationConnectorViewSet, basename="integration")
router.register("device-profiles", DeviceProfileViewSet, basename="device-profile")
router.register("industry-presets", IndustryPresetViewSet, basename="industry-preset")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/sync/", SyncView.as_view(), name="sync"),
    path("api/v1/barcodes/validate/", BarcodeValidationView.as_view(), name="barcode-validate"),
    path("api/v1/lookups/assets/", LookupView.as_view(), name="asset-lookup"),
    path("api/v1/live-data/", LiveDataView.as_view(), name="live-data"),
    path("api/v1/webhooks/inbound/", WebhookInboundView.as_view(), name="webhook-inbound"),
    # Observability & monitoring
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("alive/", LivenessProbeView.as_view(), name="liveness-probe"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
    path("api/v1/", include(router.urls)),
]
