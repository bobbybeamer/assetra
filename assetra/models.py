import hashlib
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

User = get_user_model()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.name


class TenantMembership(TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"
        AUDITOR = "auditor", "Auditor"
        READ_ONLY = "read_only", "Read Only"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tenant_memberships")
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        unique_together = ("tenant", "user")


class TenantScopedModel(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Location(TenantScopedModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class AssetCategory(TenantScopedModel):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("tenant", "code")


class Asset(TenantScopedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        IN_MAINTENANCE = "in_maintenance", "In Maintenance"
        RETIRED = "retired", "Retired"
        LOST = "lost", "Lost"

    class BarcodeType(models.TextChoices):
        GS1 = "gs1", "GS1"
        CODE128 = "code128", "Code 128"
        QR = "qr", "QR"
        DATAMATRIX = "datamatrix", "DataMatrix"

    asset_tag = models.CharField(max_length=80)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(AssetCategory, null=True, blank=True, on_delete=models.SET_NULL)
    parent_asset = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    current_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    barcode_value = models.CharField(max_length=255, blank=True)
    barcode_type = models.CharField(max_length=20, choices=BarcodeType.choices, default=BarcodeType.QR)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    custom_fields = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("tenant", "asset_tag")

    def __str__(self) -> str:
        return self.asset_tag


class AssetStateHistory(TenantScopedModel):
    class EventType(models.TextChoices):
        CREATE = "create", "Create"
        ASSIGN = "assign", "Assign"
        MOVE = "move", "Move"
        INSPECT = "inspect", "Inspect"
        MAINTAIN = "maintain", "Maintain"
        RETIRE = "retire", "Retire"
        SCAN = "scan", "Scan"
        RECONCILE = "reconcile", "Reconcile"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="history")
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    previous_state = models.JSONField(default=dict)
    new_state = models.JSONField(default=dict)
    checksum = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("AssetStateHistory is immutable")
        digest_payload = f"{self.asset_id}:{self.event_type}:{self.previous_state}:{self.new_state}"
        self.checksum = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
        return super().save(*args, **kwargs)


class ScanEvent(TenantScopedModel):
    class SourceType(models.TextChoices):
        CAMERA = "camera", "Camera"
        RFID = "rfid", "RFID"
        EXTERNAL_SCANNER = "external_scanner", "External Scanner"
        WEB = "web", "Web"

    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VALIDATED = "validated", "Validated"
        REJECTED = "rejected", "Rejected"

    client_event_id = models.UUIDField(default=uuid.uuid4)
    asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL)
    scanner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    symbology = models.CharField(max_length=50)
    raw_value = models.CharField(max_length=512)
    decoded_payload = models.JSONField(default=dict, blank=True)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    offline_captured_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ScanStatus.choices, default=ScanStatus.PENDING)
    validation_errors = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("tenant", "client_event_id")


class InventorySession(TenantScopedModel):
    class SessionStatus(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        RECONCILED = "reconciled", "Reconciled"

    name = models.CharField(max_length=200)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.OPEN)
    opened_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class InventoryCountLine(TenantScopedModel):
    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, related_name="lines")
    asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL)
    barcode_value = models.CharField(max_length=255)
    expected_qty = models.IntegerField(default=1)
    counted_qty = models.IntegerField(default=0)
    variance_qty = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.variance_qty = self.counted_qty - self.expected_qty
        return super().save(*args, **kwargs)


class MaintenanceRecord(TenantScopedModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="maintenance_records")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    performed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    result_data = models.JSONField(default=dict, blank=True)


class InspectionRecord(TenantScopedModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="inspection_records")
    inspected_at = models.DateTimeField(auto_now_add=True)
    inspector = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=100, default="pass")
    details = models.JSONField(default=dict, blank=True)


class BarcodeTemplate(TenantScopedModel):
    name = models.CharField(max_length=120)
    symbology = models.CharField(max_length=20, choices=Asset.BarcodeType.choices)
    width_mm = models.DecimalField(max_digits=8, decimal_places=2, default=50)
    height_mm = models.DecimalField(max_digits=8, decimal_places=2, default=25)
    dpi = models.IntegerField(default=300)
    text_template = models.TextField(blank=True)
    zpl_template = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)


class BarcodeBatch(TenantScopedModel):
    template = models.ForeignKey(BarcodeTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    prefix = models.CharField(max_length=20, blank=True)
    start_sequence = models.IntegerField(default=1)
    end_sequence = models.IntegerField(default=100)
    payload_schema = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    generated_at = models.DateTimeField(auto_now_add=True)


class BarcodeLabel(TenantScopedModel):
    batch = models.ForeignKey(BarcodeBatch, on_delete=models.CASCADE, related_name="labels")
    asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL)
    code_value = models.CharField(max_length=255)
    render_payload = models.JSONField(default=dict, blank=True)
    pdf_path = models.CharField(max_length=255, blank=True)
    zpl_payload = models.TextField(blank=True)


class NoCodeFormDefinition(TenantScopedModel):
    name = models.CharField(max_length=150)
    target_model = models.CharField(max_length=100)
    schema = models.JSONField(default=dict)
    required_fields = models.JSONField(default=list, blank=True)
    validation_rules = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)


class WorkflowDefinition(TenantScopedModel):
    class TriggerType(models.TextChoices):
        ON_SCAN = "on_scan", "On Scan"
        ON_STATUS_CHANGE = "on_status_change", "On Status Change"
        ON_TIME = "on_time", "On Time"

    name = models.CharField(max_length=150)
    version = models.IntegerField(default=1)
    trigger_type = models.CharField(max_length=30, choices=TriggerType.choices)
    entry_conditions = models.JSONField(default=dict, blank=True)
    steps = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)


class WorkflowRun(TenantScopedModel):
    class RunStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="runs")
    asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL)
    scan_event = models.ForeignKey(ScanEvent, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=RunStatus.choices, default=RunStatus.PENDING)
    context = models.JSONField(default=dict, blank=True)
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class WebhookEndpoint(TenantScopedModel):
    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    name = models.CharField(max_length=120)
    direction = models.CharField(max_length=20, choices=Direction.choices)
    url = models.URLField()
    secret = models.CharField(max_length=200, blank=True)
    events = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_delivery_at = models.DateTimeField(null=True, blank=True)


class WebhookDelivery(TenantScopedModel):
    class DeliveryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        DEAD_LETTER = "dead_letter", "Dead Letter"

    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_name = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    attempt_count = models.IntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    dead_lettered_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)


class IntegrationConnector(TenantScopedModel):
    class ConnectorType(models.TextChoices):
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        EXCEL = "excel", "Excel"
        ZAPIER = "zapier", "Zapier"
        MAKE = "make", "Make"
        POWER_BI = "power_bi", "Power BI"
        TABLEAU = "tableau", "Tableau"
        GRAFANA = "grafana", "Grafana"
        POSTGRESQL = "postgresql", "PostgreSQL"
        MYSQL = "mysql", "MySQL"
        SQL_SERVER = "sql_server", "SQL Server"
        ORACLE = "oracle", "Oracle"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=120)
    connector_type = models.CharField(max_length=30, choices=ConnectorType.choices)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)


class DeviceProfile(TenantScopedModel):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"
        WEB = "web", "Web"

    name = models.CharField(max_length=120)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    device_identifier = models.CharField(max_length=120)
    sdk_features = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("tenant", "device_identifier")


class FeatureFlag(TenantScopedModel):
    key = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=False)
    conditions = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("tenant", "key")


class IndustryPreset(TenantScopedModel):
    class PresetType(models.TextChoices):
        MEDICAL = "medical", "Medical"
        MAINTENANCE = "maintenance", "Maintenance"
        GENERAL = "general", "General"

    name = models.CharField(max_length=120)
    preset_type = models.CharField(max_length=20, choices=PresetType.choices)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
