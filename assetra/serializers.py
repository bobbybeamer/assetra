from rest_framework import serializers

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
    WebhookEndpoint,
    WorkflowDefinition,
    WorkflowRun,
)
from .services import validate_workflow_definition


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = "__all__"


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class AssetSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Asset
        fields = "__all__"

    def validate(self, attrs):
        request = self.context.get("request")
        tenant_id = request.headers.get("X-Tenant-ID") if request else None

        def _must_match_tenant(field_name):
            obj = attrs.get(field_name)
            if obj and str(getattr(obj, "tenant_id", "")) != str(tenant_id):
                raise serializers.ValidationError({field_name: "must belong to current tenant"})

        for field in ("category", "current_location", "parent_asset"):
            _must_match_tenant(field)

        assigned_to = attrs.get("assigned_to")
        if assigned_to and tenant_id:
            is_member = TenantMembership.objects.filter(tenant_id=tenant_id, user=assigned_to).exists()
            if not is_member:
                raise serializers.ValidationError({"assigned_to": "user must be a member of current tenant"})

        return attrs


class AssetStateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetStateHistory
        fields = "__all__"
        read_only_fields = ("checksum", "created_at")


class ScanEventSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ScanEvent
        fields = "__all__"

    def validate(self, attrs):
        request = self.context.get("request")
        tenant_id = request.headers.get("X-Tenant-ID") if request else None

        asset = attrs.get("asset")
        if asset and str(asset.tenant_id) != str(tenant_id):
            raise serializers.ValidationError({"asset": "must belong to current tenant"})

        location = attrs.get("location")
        if location and str(location.tenant_id) != str(tenant_id):
            raise serializers.ValidationError({"location": "must belong to current tenant"})

        return attrs


class InventorySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySession
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}

    def validate(self, attrs):
        trigger_type = attrs.get("trigger_type", getattr(self.instance, "trigger_type", None))
        entry_conditions = attrs.get("entry_conditions", getattr(self.instance, "entry_conditions", {}))
        steps = attrs.get("steps", getattr(self.instance, "steps", []))

        errors = validate_workflow_definition(
            trigger_type=trigger_type,
            entry_conditions=entry_conditions,
            steps=steps,
        )
        if errors:
            raise serializers.ValidationError({"workflow": errors})
        return attrs


class WorkflowRunSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source="workflow.name", read_only=True)
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)

    class Meta:
        model = WorkflowRun
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class NoCodeFormDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoCodeFormDefinition
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class BarcodeBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarcodeBatch
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}, "generated_by": {"required": False}}


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class IntegrationConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationConnector
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class DeviceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceProfile
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class IndustryPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryPreset
        fields = "__all__"
        extra_kwargs = {"tenant": {"required": False}}


class SyncPayloadSerializer(serializers.Serializer):
    last_sync_at = serializers.DateTimeField(required=False)
    scan_events = ScanEventSerializer(many=True, required=False)
    conflict_acknowledgements = serializers.ListField(child=serializers.DictField(), required=False)
