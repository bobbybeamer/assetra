from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Asset,
    AssetCategory,
    AssetStateHistory,
    BarcodeBatch,
    DeviceProfile,
    IndustryPreset,
    IntegrationConnector,
    InventorySession,
    Location,
    NoCodeFormDefinition,
    ScanEvent,
    Tenant,
    TenantMembership,
    WebhookDelivery,
    WebhookEndpoint,
    WorkflowDefinition,
    WorkflowRun,
)
from .permissions import TenantRBACPermission
from .serializers import (
    AssetCategorySerializer,
    AssetSerializer,
    BarcodeBatchSerializer,
    DeviceProfileSerializer,
    IndustryPresetSerializer,
    IntegrationConnectorSerializer,
    InventorySessionSerializer,
    LocationSerializer,
    NoCodeFormDefinitionSerializer,
    ScanEventSerializer,
    SyncPayloadSerializer,
    TenantSerializer,
    WebhookEndpointSerializer,
    WorkflowDefinitionSerializer,
    WorkflowRunSerializer,
)
from .services import decode_barcode, dry_run_workflow, execute_triggered_workflows, validate_barcode
from .tasks import dispatch_webhook, generate_barcode_batch


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [TenantRBACPermission]
    filterset_fields = ["tenant"]
    search_fields = ["id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return queryset.filter(tenant_id=tenant_id)
        return queryset.none()

    def perform_create(self, serializer):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        serializer.save(tenant_id=tenant_id)


class TenantViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Tenant.objects.all().order_by("name")
    serializer_class = TenantSerializer
    permission_classes = [TenantRBACPermission]


class LocationViewSet(TenantScopedViewSet):
    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    search_fields = ["name", "code"]


class AssetCategoryViewSet(TenantScopedViewSet):
    queryset = AssetCategory.objects.all().order_by("name")
    serializer_class = AssetCategorySerializer
    search_fields = ["name", "code"]


class AssetViewSet(TenantScopedViewSet):
    queryset = Asset.objects.select_related("category", "current_location", "assigned_to").all()
    serializer_class = AssetSerializer
    search_fields = ["asset_tag", "name", "barcode_value"]
    filterset_fields = ["tenant", "status", "category", "current_location"]

    def perform_update(self, serializer):
        asset_before = self.get_object()
        previous_status = asset_before.status
        previous_state = {
            "status": asset_before.status,
            "assigned_to": asset_before.assigned_to_id,
            "location": asset_before.current_location_id,
        }
        asset_after = serializer.save()
        new_state = {
            "status": asset_after.status,
            "assigned_to": asset_after.assigned_to_id,
            "location": asset_after.current_location_id,
        }
        AssetStateHistory.objects.create(
            tenant=asset_after.tenant,
            asset=asset_after,
            event_type=AssetStateHistory.EventType.MOVE,
            actor=self.request.user,
            location=asset_after.current_location,
            previous_state=previous_state,
            new_state=new_state,
        )
        if previous_status != asset_after.status:
            execute_triggered_workflows(
                tenant_id=asset_after.tenant_id,
                trigger_type=WorkflowDefinition.TriggerType.ON_STATUS_CHANGE,
                actor=self.request.user,
                asset=asset_after,
                extra_context={
                    "previous_status": previous_status,
                    "new_status": asset_after.status,
                },
            )


class ScanEventViewSet(TenantScopedViewSet):
    queryset = ScanEvent.objects.select_related("asset", "scanner", "location").all()
    serializer_class = ScanEventSerializer
    search_fields = ["raw_value", "symbology"]
    filterset_fields = ["tenant", "status", "source_type", "asset"]

    def perform_create(self, serializer):
        decoded = decode_barcode(serializer.validated_data["symbology"], serializer.validated_data["raw_value"])
        errors = validate_barcode(serializer.validated_data["symbology"], serializer.validated_data["raw_value"])
        status_value = ScanEvent.ScanStatus.REJECTED if errors else ScanEvent.ScanStatus.VALIDATED
        scan = serializer.save(
            tenant_id=self.request.headers.get("X-Tenant-ID"),
            scanner=self.request.user,
            decoded_payload=decoded,
            validation_errors=errors,
            status=status_value,
            synced_at=timezone.now(),
        )
        if scan.asset_id:
            AssetStateHistory.objects.create(
                tenant=scan.tenant,
                asset=scan.asset,
                event_type=AssetStateHistory.EventType.SCAN,
                actor=self.request.user,
                location=scan.location,
                gps_latitude=scan.gps_latitude,
                gps_longitude=scan.gps_longitude,
                previous_state={"status": scan.asset.status},
                new_state={"status": scan.asset.status, "last_scan": str(scan.id)},
            )
        execute_triggered_workflows(
            tenant_id=scan.tenant_id,
            trigger_type=WorkflowDefinition.TriggerType.ON_SCAN,
            actor=self.request.user,
            asset=scan.asset,
            scan_event=scan,
            extra_context={
                "scan_event": {
                    "id": scan.id,
                    "symbology": scan.symbology,
                    "raw_value": scan.raw_value,
                    "source_type": scan.source_type,
                }
            },
        )


class InventorySessionViewSet(TenantScopedViewSet):
    queryset = InventorySession.objects.all().order_by("-opened_at")
    serializer_class = InventorySessionSerializer
    filterset_fields = ["tenant", "status", "location"]


class WorkflowDefinitionViewSet(TenantScopedViewSet):
    queryset = WorkflowDefinition.objects.all().order_by("name")
    serializer_class = WorkflowDefinitionSerializer
    search_fields = ["name", "trigger_type"]

    @action(detail=True, methods=["post"], url_path="execute")
    def execute_workflow(self, request, pk=None):
        workflow = self.get_object()
        tenant_id = request.headers.get("X-Tenant-ID")
        dry_run = bool(request.data.get("dry_run", False))
        force_run = bool(request.data.get("force", False))
        asset = None
        scan_event = None

        asset_id = request.data.get("asset_id")
        if asset_id:
            asset = Asset.objects.filter(id=asset_id, tenant_id=tenant_id).first()
            if not asset:
                return Response({"detail": "asset not found"}, status=status.HTTP_404_NOT_FOUND)

        scan_event_id = request.data.get("scan_event_id")
        if scan_event_id:
            scan_event = ScanEvent.objects.filter(id=scan_event_id, tenant_id=tenant_id).first()
            if not scan_event:
                return Response({"detail": "scan event not found"}, status=status.HTTP_404_NOT_FOUND)

        if dry_run:
            preview = dry_run_workflow(
                workflow=workflow,
                asset=asset,
                scan_event=scan_event,
                extra_context=request.data.get("context", {}),
                force_run=force_run,
            )
            return Response({"dry_run": True, "preview": preview}, status=status.HTTP_200_OK)

        run_ids = execute_triggered_workflows(
            tenant_id=tenant_id,
            trigger_type=workflow.trigger_type,
            actor=request.user,
            asset=asset,
            scan_event=scan_event,
            extra_context=request.data.get("context", {}),
            workflow_definition_id=workflow.id,
            force_run=force_run,
        )
        runs = WorkflowRun.objects.filter(id__in=run_ids).order_by("-id")
        return Response({"run_count": len(run_ids), "runs": WorkflowRunSerializer(runs, many=True).data}, status=status.HTTP_200_OK)


class WorkflowRunViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [TenantRBACPermission]
    queryset = WorkflowRun.objects.select_related("workflow", "asset", "scan_event").all().order_by("-started_at")
    serializer_class = WorkflowRunSerializer
    filterset_fields = ["tenant", "status", "workflow", "asset", "scan_event"]
    search_fields = ["workflow__name", "asset__asset_tag"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        queryset = super().get_queryset()
        if tenant_id:
            return queryset.filter(tenant_id=tenant_id)
        return queryset.none()


class NoCodeFormDefinitionViewSet(TenantScopedViewSet):
    queryset = NoCodeFormDefinition.objects.all().order_by("name")
    serializer_class = NoCodeFormDefinitionSerializer
    search_fields = ["name", "target_model"]


class BarcodeBatchViewSet(TenantScopedViewSet):
    queryset = BarcodeBatch.objects.all().order_by("-generated_at")
    serializer_class = BarcodeBatchSerializer

    def perform_create(self, serializer):
        batch = serializer.save(tenant_id=self.request.headers.get("X-Tenant-ID"), generated_by=self.request.user)
        generate_barcode_batch.delay(batch.id)


class WebhookEndpointViewSet(TenantScopedViewSet):
    queryset = WebhookEndpoint.objects.all().order_by("name")
    serializer_class = WebhookEndpointSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        endpoint = serializer.save(tenant_id=self.request.headers.get("X-Tenant-ID"))
        if endpoint.direction == WebhookEndpoint.Direction.OUTBOUND:
            dispatch_webhook.delay(endpoint.id, "webhook.created", {"endpoint_id": endpoint.id})


class IntegrationConnectorViewSet(TenantScopedViewSet):
    queryset = IntegrationConnector.objects.all().order_by("name")
    serializer_class = IntegrationConnectorSerializer


class DeviceProfileViewSet(TenantScopedViewSet):
    queryset = DeviceProfile.objects.all().order_by("name")
    serializer_class = DeviceProfileSerializer


class IndustryPresetViewSet(TenantScopedViewSet):
    queryset = IndustryPreset.objects.all().order_by("name")
    serializer_class = IndustryPresetSerializer


class SyncView(APIView):
    permission_classes = [TenantRBACPermission]

    def post(self, request):
        serializer = SyncPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant_id = request.headers.get("X-Tenant-ID")
        now = timezone.now()

        pushed = []
        for scan in serializer.validated_data.get("scan_events", []):
            scan_obj, _created = ScanEvent.objects.update_or_create(
                tenant_id=tenant_id,
                client_event_id=scan["client_event_id"],
                defaults={
                    **scan,
                    "tenant_id": tenant_id,
                    "scanner": request.user,
                    "synced_at": now,
                },
            )
            pushed.append(scan_obj.id)

        last_sync_at = serializer.validated_data.get("last_sync_at")
        conflict_acks = serializer.validated_data.get("conflict_acknowledgements", [])
        changes_qs = Asset.objects.filter(tenant_id=tenant_id)
        if last_sync_at:
            changes_qs = changes_qs.filter(updated_at__gt=last_sync_at)
        changes = AssetSerializer(changes_qs.order_by("updated_at")[:500], many=True).data

        return Response(
            {
                "server_time": now,
                "accepted_scan_event_ids": pushed,
                "asset_changes": changes,
                "acknowledged_conflicts": conflict_acks,
                "conflict_strategy": "last-write-wins-with-history",
            },
            status=status.HTTP_200_OK,
        )


class BarcodeValidationView(APIView):
    permission_classes = [TenantRBACPermission]

    def post(self, request):
        symbology = request.data.get("symbology", "")
        raw_value = request.data.get("raw_value", "")
        decoded = decode_barcode(symbology, raw_value)
        errors = validate_barcode(symbology, raw_value)
        return Response(
            {
                "valid": len(errors) == 0,
                "errors": errors,
                "decoded": decoded,
            },
            status=status.HTTP_200_OK,
        )


class LookupView(APIView):
    permission_classes = [TenantRBACPermission]

    def get(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")
        barcode = request.query_params.get("barcode")
        if not barcode:
            return Response({"detail": "barcode query param is required"}, status=status.HTTP_400_BAD_REQUEST)
        asset = Asset.objects.filter(tenant_id=tenant_id, barcode_value=barcode).first()
        if not asset:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(AssetSerializer(asset).data, status=status.HTTP_200_OK)


class LiveDataView(APIView):
    permission_classes = [TenantRBACPermission]

    def get(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")
        asset_data = AssetSerializer(Asset.objects.filter(tenant_id=tenant_id).order_by("-updated_at")[:100], many=True).data
        scan_data = ScanEventSerializer(ScanEvent.objects.filter(tenant_id=tenant_id).order_by("-created_at")[:100], many=True).data
        return Response({"assets": asset_data, "scan_events": scan_data}, status=status.HTTP_200_OK)


class AuthContextView(APIView):
    permission_classes = [TenantRBACPermission]

    def get(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")
        membership = TenantMembership.objects.filter(tenant_id=tenant_id, user=request.user).first()
        if not membership:
            return Response({"detail": "membership not found"}, status=status.HTTP_404_NOT_FOUND)

        can_write = membership.role in {
            TenantMembership.Role.ADMIN,
            TenantMembership.Role.OPERATOR,
        }

        return Response(
            {
                "username": request.user.get_username(),
                "tenant_id": str(tenant_id),
                "role": membership.role,
                "can_write": can_write,
            },
            status=status.HTTP_200_OK,
        )


class WebhookInboundView(APIView):
    permission_classes = [TenantRBACPermission]

    def post(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")
        endpoint_id = request.data.get("endpoint_id")
        event_name = request.data.get("event_name", "inbound.event")
        endpoint = WebhookEndpoint.objects.filter(tenant_id=tenant_id, id=endpoint_id, direction=WebhookEndpoint.Direction.INBOUND).first()
        if not endpoint:
            return Response({"detail": "Inbound endpoint not found"}, status=status.HTTP_404_NOT_FOUND)
        delivery = WebhookDelivery.objects.create(
            tenant_id=tenant_id,
            endpoint=endpoint,
            event_name=event_name,
            payload=request.data.get("payload", {}),
            status=WebhookDelivery.DeliveryStatus.SUCCESS,
            response_code=202,
            response_body="accepted",
            delivered_at=timezone.now(),
        )
        return Response({"delivery_id": delivery.id, "status": "accepted"}, status=status.HTTP_202_ACCEPTED)


# ============================================================================
# OBSERVABILITY & HEALTH CHECKS
# ============================================================================

class HealthCheckView(APIView):
    """Full health check for all system components."""
    
    permission_classes = []  # No auth required for health checks
    authentication_classes = []
    
    def get(self, request):
        from .observability import health_check_all
        
        health = health_check_all()
        status_code = status.HTTP_200_OK if health['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(health, status=status_code)


class LivenessProbeView(APIView):
    """Kubernetes liveness probe for container health."""
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        return Response({"status": "alive"}, status=status.HTTP_200_OK)


class MetricsView(APIView):
    """Prometheus metrics endpoint."""
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        # Generate Prometheus metrics
        metrics_output = generate_latest()
        
        return Response(
            metrics_output.decode('utf-8'),
            status=status.HTTP_200_OK,
            content_type=CONTENT_TYPE_LATEST
        )
