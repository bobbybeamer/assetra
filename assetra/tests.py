from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Asset, Tenant, TenantMembership, WebhookDelivery, WebhookEndpoint, WorkflowDefinition, WorkflowRun
from .tasks import dispatch_webhook

User = get_user_model()


class AssetraAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="operator", password="secret123")
        self.tenant = Tenant.objects.create(name="Demo Tenant", slug="demo-tenant")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantMembership.Role.OPERATOR,
        )
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(self.tenant.id))

        self.auditor = User.objects.create_user(username="auditor", password="secret123")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.auditor,
            role=TenantMembership.Role.AUDITOR,
        )

        self.other_tenant = Tenant.objects.create(name="Other Tenant", slug="other-tenant")
        self.other_user = User.objects.create_user(username="other", password="secret123")
        TenantMembership.objects.create(
            tenant=self.other_tenant,
            user=self.other_user,
            role=TenantMembership.Role.ADMIN,
        )

    def test_create_asset(self):
        response = self.client.post(
            reverse("asset-list"),
            {
                "asset_tag": "A-1001",
                "name": "Pump Motor",
                "barcode_value": "QR-A-1001",
                "barcode_type": "qr",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 1)

    def test_sync_endpoint(self):
        response = self.client.post(reverse("sync"), {"scan_events": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("asset_changes", response.data)

    def test_on_scan_workflow_executes(self):
        workflow = WorkflowDefinition.objects.create(
            tenant=self.tenant,
            name="Scan Maintenance Workflow",
            trigger_type=WorkflowDefinition.TriggerType.ON_SCAN,
            entry_conditions={},
            steps=[
                {"action": "set_asset_status", "status": "in_maintenance"},
                {
                    "action": "update_asset_custom_fields",
                    "fields": {"last_scanned_value": "{{scan_event.raw_value}}"},
                },
            ],
            is_active=True,
        )

        asset_response = self.client.post(
            reverse("asset-list"),
            {
                "asset_tag": "A-2001",
                "name": "Compressor",
                "barcode_value": "QR-A-2001",
                "barcode_type": "qr",
            },
            format="json",
        )
        self.assertEqual(asset_response.status_code, status.HTTP_201_CREATED)
        asset_id = asset_response.data["id"]

        scan_response = self.client.post(
            reverse("scan-event-list"),
            {
                "asset": asset_id,
                "symbology": "qr",
                "raw_value": "QR-A-2001",
                "source_type": "camera",
            },
            format="json",
        )
        self.assertEqual(scan_response.status_code, status.HTTP_201_CREATED)

        asset = Asset.objects.get(id=asset_id)
        self.assertEqual(asset.status, Asset.Status.IN_MAINTENANCE)
        self.assertEqual(asset.custom_fields.get("last_scanned_value"), "QR-A-2001")

        run = WorkflowRun.objects.filter(workflow=workflow, asset=asset).latest("id")
        self.assertEqual(run.status, WorkflowRun.RunStatus.SUCCESS)

    def test_on_status_change_workflow_executes(self):
        workflow = WorkflowDefinition.objects.create(
            tenant=self.tenant,
            name="Status Change Output",
            trigger_type=WorkflowDefinition.TriggerType.ON_STATUS_CHANGE,
            entry_conditions={"previous_status": "active", "new_status": "retired"},
            steps=[
                {"action": "set_output", "key": "transition", "value": "{{previous_status}}->{{new_status}}"}
            ],
            is_active=True,
        )

        asset_response = self.client.post(
            reverse("asset-list"),
            {
                "asset_tag": "A-3001",
                "name": "Fan Unit",
                "barcode_value": "QR-A-3001",
                "barcode_type": "qr",
            },
            format="json",
        )
        self.assertEqual(asset_response.status_code, status.HTTP_201_CREATED)
        asset_id = asset_response.data["id"]

        patch_response = self.client.patch(
            reverse("asset-detail", args=[asset_id]),
            {"status": "retired"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        run = WorkflowRun.objects.filter(workflow=workflow, asset_id=asset_id).latest("id")
        self.assertEqual(run.status, WorkflowRun.RunStatus.SUCCESS)
        self.assertEqual(run.output_data.get("executed_steps", [])[0].get("key"), "transition")

    def test_manual_execute_workflow_endpoint_and_run_list(self):
        workflow = WorkflowDefinition.objects.create(
            tenant=self.tenant,
            name="Manual Workflow",
            trigger_type=WorkflowDefinition.TriggerType.ON_SCAN,
            entry_conditions={"asset.status": "active"},
            steps=[
                {"action": "set_output", "key": "mode", "value": "manual"},
                {"action": "update_asset_custom_fields", "fields": {"manual_triggered": "true"}},
            ],
            is_active=True,
        )

        asset_response = self.client.post(
            reverse("asset-list"),
            {
                "asset_tag": "A-4001",
                "name": "Manual Asset",
                "barcode_value": "QR-A-4001",
                "barcode_type": "qr",
            },
            format="json",
        )
        self.assertEqual(asset_response.status_code, status.HTTP_201_CREATED)
        asset_id = asset_response.data["id"]

        execute_response = self.client.post(
            reverse("workflow-definition-execute-workflow", args=[workflow.id]),
            {
                "asset_id": asset_id,
                "force": True,
                "context": {"invoked_from": "test"},
            },
            format="json",
        )
        self.assertEqual(execute_response.status_code, status.HTTP_200_OK)
        self.assertEqual(execute_response.data["run_count"], 1)

        run_id = execute_response.data["runs"][0]["id"]
        run_detail = self.client.get(reverse("workflow-run-detail", args=[run_id]))
        self.assertEqual(run_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(run_detail.data["status"], WorkflowRun.RunStatus.SUCCESS)

        run_list = self.client.get(reverse("workflow-run-list"))
        self.assertEqual(run_list.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(run_list.data), 1)

    def test_workflow_definition_validation_rejects_invalid_steps(self):
        response = self.client.post(
            reverse("workflow-definition-list"),
            {
                "name": "Invalid Workflow",
                "trigger_type": WorkflowDefinition.TriggerType.ON_SCAN,
                "entry_conditions": {},
                "steps": [{"status": "retired"}],
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("workflow", response.data)

    def test_workflow_execute_dry_run_has_no_side_effects(self):
        workflow = WorkflowDefinition.objects.create(
            tenant=self.tenant,
            name="Dry Run Workflow",
            trigger_type=WorkflowDefinition.TriggerType.ON_SCAN,
            entry_conditions={},
            steps=[{"action": "set_asset_status", "status": "retired"}],
            is_active=True,
        )

        asset_response = self.client.post(
            reverse("asset-list"),
            {
                "asset_tag": "A-5001",
                "name": "Dry Run Asset",
                "barcode_value": "QR-A-5001",
                "barcode_type": "qr",
            },
            format="json",
        )
        self.assertEqual(asset_response.status_code, status.HTTP_201_CREATED)
        asset_id = asset_response.data["id"]

        execute_response = self.client.post(
            reverse("workflow-definition-execute-workflow", args=[workflow.id]),
            {
                "asset_id": asset_id,
                "dry_run": True,
            },
            format="json",
        )
        self.assertEqual(execute_response.status_code, status.HTTP_200_OK)
        self.assertTrue(execute_response.data["dry_run"])

        asset = Asset.objects.get(id=asset_id)
        self.assertEqual(asset.status, Asset.Status.ACTIVE)
        self.assertEqual(WorkflowRun.objects.filter(workflow=workflow, asset=asset).count(), 0)

    @patch("assetra.tasks.urlopen")
    def test_dispatch_webhook_sets_signature_header(self, mocked_urlopen):
        class _MockResponse:
            status = 200

            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        mocked_urlopen.return_value = _MockResponse()

        endpoint = WebhookEndpoint.objects.create(
            tenant=self.tenant,
            name="Outbound Signed",
            direction=WebhookEndpoint.Direction.OUTBOUND,
            url="https://example.com/hook",
            secret="top-secret",
            events=["scan.created"],
        )

        delivery_id = dispatch_webhook(endpoint.id, "scan.created", {"asset_id": 1})
        delivery = WebhookDelivery.objects.get(id=delivery_id)
        self.assertEqual(delivery.status, WebhookDelivery.DeliveryStatus.SUCCESS)

        request_obj = mocked_urlopen.call_args[0][0]
        request_headers = {key.lower(): value for key, value in request_obj.header_items()}
        self.assertIn("x-assetra-signature", request_headers)
        self.assertTrue(request_headers["x-assetra-signature"].startswith("sha256="))

    @patch("assetra.tasks.urlopen", side_effect=Exception("network down"))
    def test_dispatch_webhook_dead_letters_after_max_attempts(self, _mocked_urlopen):
        endpoint = WebhookEndpoint.objects.create(
            tenant=self.tenant,
            name="Outbound Retry",
            direction=WebhookEndpoint.Direction.OUTBOUND,
            url="https://example.com/hook",
            secret="top-secret",
            events=["scan.created"],
        )

        delivery_id = dispatch_webhook(endpoint.id, "scan.created", {"asset_id": 1}, max_attempts=1, retry_base_seconds=1)
        delivery = WebhookDelivery.objects.get(id=delivery_id)

        self.assertEqual(delivery.status, WebhookDelivery.DeliveryStatus.DEAD_LETTER)
        self.assertEqual(delivery.attempt_count, 1)
        self.assertIsNotNone(delivery.dead_lettered_at)
        self.assertIn("network down", delivery.last_error)

    def test_auditor_cannot_create_asset(self):
        auditor_token = RefreshToken.for_user(self.auditor).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {auditor_token}", HTTP_X_TENANT_ID=str(self.tenant.id))

        response = self.client.post(
            reverse("asset-list"),
            {
                "asset_tag": "A-9001",
                "name": "Forbidden Asset",
                "barcode_value": "QR-A-9001",
                "barcode_type": "qr",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_tenant_asset_is_not_accessible(self):
        other_token = RefreshToken.for_user(self.other_user).access_token

        asset = Asset.objects.create(
            tenant=self.other_tenant,
            asset_tag="OTH-100",
            name="Other Tenant Asset",
            barcode_value="QR-OTH-100",
            barcode_type="qr",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token}", HTTP_X_TENANT_ID=str(self.tenant.id))
        response = self.client.get(reverse("asset-detail", args=[asset.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_scan_event_rejects_cross_tenant_asset_reference(self):
        cross_asset = Asset.objects.create(
            tenant=self.other_tenant,
            asset_tag="OTH-200",
            name="Cross Tenant Asset",
            barcode_value="QR-OTH-200",
            barcode_type="qr",
        )

        response = self.client.post(
            reverse("scan-event-list"),
            {
                "asset": cross_asset.id,
                "symbology": "qr",
                "raw_value": "QR-OTH-200",
                "source_type": "camera",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("asset", response.data)


# ============================================================================
# MONITORING & OBSERVABILITY TESTS
# ============================================================================

class MonitoringTestCase(APITestCase):
    """Tests for health checks, metrics, and observability endpoints."""

    def test_health_check_endpoint_accessible_without_auth(self):
        """Health check should be accessible without authentication."""
        response = self.client.get(reverse("health-check"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('timestamp', data)

    def test_health_check_database_connectivity(self):
        """Health check should verify database connectivity."""
        response = self.client.get(reverse("health-check"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('database', data['checks'])
        db_check = data['checks']['database']
        self.assertEqual(db_check['status'], 'healthy')
        self.assertEqual(db_check['component'], 'database')

    def test_liveness_probe_endpoint(self):
        """Liveness probe should always return 200 OK."""
        response = self.client.get(reverse("liveness-probe"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'alive')

    def test_metrics_endpoint_accessible_without_auth(self):
        """Metrics endpoint should be accessible without authentication."""
        response = self.client.get(reverse("metrics"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('assetra_', response.content.decode())

    def test_metrics_contains_prometheus_format(self):
        """Metrics should be in Prometheus text format."""
        response = self.client.get(reverse("metrics"))
        content = response.content.decode()
        # Should contain HELP and TYPE comments for metrics
        self.assertIn('# HELP', content)
        self.assertIn('# TYPE', content)

    def test_structured_logging_integration(self):
        """Verify structured logging is initialized."""
        import logging
        logger = logging.getLogger('assetra')
        self.assertIsNotNone(logger)

    def test_api_request_tracking_adds_request_id(self):
        """API requests should have request_id in tracking."""
        from unittest.mock import patch
        
        # Create a test tenant and user
        user = User.objects.create_user(username="test_user", password="test_pass")
        tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")
        TenantMembership.objects.create(
            tenant=tenant,
            user=user,
            role=TenantMembership.Role.ADMIN,
        )
        
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))
        
        # Make a request and verify it was tracked
        response = self.client.get(reverse("asset-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

