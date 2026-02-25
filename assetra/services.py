from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Asset, AssetStateHistory, WorkflowDefinition, WorkflowRun
from .observability import track_workflow_execution, workflow_executions_total


SUPPORTED_WORKFLOW_ACTIONS = {
    "validate_required_fields",
    "set_asset_status",
    "update_asset_custom_fields",
    "create_history",
    "set_output",
}


def validate_workflow_definition(*, trigger_type: str, entry_conditions: dict, steps: list) -> list[str]:
    errors: list[str] = []
    if trigger_type not in dict(WorkflowDefinition.TriggerType.choices):
        errors.append("trigger_type is invalid")

    if not isinstance(entry_conditions, dict):
        errors.append("entry_conditions must be an object")

    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty list")
        return errors

    allowed_event_types = set(dict(AssetStateHistory.EventType.choices).keys())

    for index, step in enumerate(steps):
        step_ref = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{step_ref} must be an object")
            continue

        action = step.get("action")
        if action not in SUPPORTED_WORKFLOW_ACTIONS:
            errors.append(f"{step_ref}.action is unsupported")
            continue

        if action == "validate_required_fields" and (not isinstance(step.get("fields"), list) or not step.get("fields")):
            errors.append(f"{step_ref}.fields must be a non-empty list")

        if action == "set_asset_status" and step.get("status") not in dict(Asset.Status.choices):
            errors.append(f"{step_ref}.status is invalid")

        if action == "update_asset_custom_fields" and not isinstance(step.get("fields"), dict):
            errors.append(f"{step_ref}.fields must be an object")

        if action == "create_history" and step.get("event_type") and step.get("event_type") not in allowed_event_types:
            errors.append(f"{step_ref}.event_type is invalid")

        if action == "set_output":
            if not step.get("key"):
                errors.append(f"{step_ref}.key is required")
            if "value" not in step:
                errors.append(f"{step_ref}.value is required")

    return errors


def decode_barcode(symbology: str, raw_value: str) -> dict:
    """Centralized decoding service for camera/RFID/enterprise scanners.

    This function is intentionally simple in scaffold form; production
    implementations can plug in specialized GS1 parsers or device SDK decoders.
    """
    payload = {"symbology": symbology, "raw": raw_value, "decoded_at": datetime.utcnow().isoformat()}
    if symbology.lower() == "gs1":
        payload["segments"] = raw_value.split("(")
    return payload


def validate_barcode(symbology: str, raw_value: str) -> list[str]:
    errors: list[str] = []
    if not raw_value:
        errors.append("raw_value is required")
    if symbology.lower() not in {"gs1", "code128", "qr", "datamatrix"}:
        errors.append("unsupported symbology")
    if len(raw_value) > 512:
        errors.append("raw_value exceeds max length")
    return errors


def render_zpl(template: str, context: dict) -> str:
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def _resolve_context_path(context: dict, path: str):
    current = context
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _render_value(value, context: dict):
    if not isinstance(value, str):
        return value
    if value.startswith("{{") and value.endswith("}}"):
        token = value[2:-2].strip()
        resolved = _resolve_context_path(context, token)
        return resolved if resolved is not None else ""
    return value


def _json_safe(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "pk"):
        return value.pk
    return str(value)


def _entry_conditions_match(entry_conditions: dict, context: dict) -> bool:
    for key, expected in entry_conditions.items():
        actual = _resolve_context_path(context, key)
        if actual != expected:
            return False
    return True


def _execute_step(step: dict, run: WorkflowRun, context: dict, actor=None):
    action = step.get("action")
    if action == "validate_required_fields":
        fields = step.get("fields", [])
        source_path = step.get("source", "asset.custom_fields")
        source_data = _resolve_context_path(context, source_path) or {}
        missing = [field for field in fields if not source_data.get(field)]
        if missing:
            raise ValidationError(f"missing required fields: {', '.join(missing)}")
        return {"action": action, "missing": []}

    if action == "set_asset_status":
        asset = context.get("asset")
        new_status = step.get("status")
        if not asset:
            raise ValidationError("asset is required for set_asset_status")
        if new_status not in dict(asset.Status.choices):
            raise ValidationError("invalid asset status")
        previous_state = {"status": asset.status}
        asset.status = new_status
        asset.save(update_fields=["status", "updated_at"])
        AssetStateHistory.objects.create(
            tenant=asset.tenant,
            asset=asset,
            event_type=AssetStateHistory.EventType.MAINTAIN,
            actor=actor,
            location=asset.current_location,
            previous_state=previous_state,
            new_state={"status": new_status},
        )
        context["asset"] = asset
        return {"action": action, "status": new_status}

    if action == "update_asset_custom_fields":
        asset = context.get("asset")
        field_map = step.get("fields", {})
        if not asset:
            raise ValidationError("asset is required for update_asset_custom_fields")
        custom_fields = dict(asset.custom_fields or {})
        for key, value in field_map.items():
            custom_fields[key] = _render_value(value, context)
        asset.custom_fields = custom_fields
        asset.save(update_fields=["custom_fields", "updated_at"])
        context["asset"] = asset
        return {"action": action, "updated_keys": list(field_map.keys())}

    if action == "create_history":
        asset = context.get("asset")
        event_type = step.get("event_type", AssetStateHistory.EventType.INSPECT)
        if not asset:
            raise ValidationError("asset is required for create_history")
        previous_state = step.get("previous_state", {"status": asset.status})
        new_state = step.get("new_state", {"status": asset.status})
        AssetStateHistory.objects.create(
            tenant=asset.tenant,
            asset=asset,
            event_type=event_type,
            actor=actor,
            location=asset.current_location,
            previous_state=previous_state,
            new_state=new_state,
        )
        return {"action": action, "event_type": event_type}

    if action == "set_output":
        key = step.get("key")
        value = _render_value(step.get("value"), context)
        if not key:
            raise ValidationError("set_output requires key")
        output_data = dict(run.output_data or {})
        output_data[key] = value
        run.output_data = output_data
        run.save(update_fields=["output_data", "updated_at"])
        return {"action": action, "key": key}

    raise ValidationError(f"unsupported workflow action: {action}")


def _simulate_step(step: dict, context: dict):
    action = step.get("action")

    if action == "validate_required_fields":
        fields = step.get("fields", [])
        source_path = step.get("source", "asset.custom_fields")
        source_data = _resolve_context_path(context, source_path) or {}
        missing = [field for field in fields if not source_data.get(field)]
        return {"action": action, "ok": len(missing) == 0, "missing": missing}

    if action == "set_asset_status":
        asset = context.get("asset")
        new_status = step.get("status")
        return {
            "action": action,
            "from_status": getattr(asset, "status", None),
            "to_status": new_status,
            "ok": asset is not None,
        }

    if action == "update_asset_custom_fields":
        asset = context.get("asset")
        existing = dict(getattr(asset, "custom_fields", {}) or {})
        field_map = step.get("fields", {})
        for key, value in field_map.items():
            existing[key] = _render_value(value, context)
        return {
            "action": action,
            "ok": asset is not None,
            "preview_custom_fields": existing,
        }

    if action == "create_history":
        return {
            "action": action,
            "ok": context.get("asset") is not None,
            "event_type": step.get("event_type", AssetStateHistory.EventType.INSPECT),
        }

    if action == "set_output":
        return {
            "action": action,
            "ok": bool(step.get("key")),
            "key": step.get("key"),
            "value": _render_value(step.get("value"), context),
        }

    raise ValidationError(f"unsupported workflow action: {action}")


def dry_run_workflow(*, workflow: WorkflowDefinition, asset=None, scan_event=None, extra_context=None, force_run: bool = False) -> dict:
    context = {
        "asset": asset,
        "scan_event": scan_event,
        "trigger_type": workflow.trigger_type,
    }
    if extra_context:
        context.update(extra_context)

    matches = _entry_conditions_match(workflow.entry_conditions or {}, context)
    if not matches and not force_run:
        return {
            "matched_entry_conditions": False,
            "forced": False,
            "simulated_steps": [],
            "message": "Entry conditions did not match",
        }

    simulated_steps = []
    for step in workflow.steps or []:
        simulated_steps.append(_simulate_step(step, context))

    return {
        "matched_entry_conditions": matches,
        "forced": force_run,
        "simulated_steps": simulated_steps,
        "message": "Dry run successful",
    }


def execute_triggered_workflows(
    *,
    tenant_id,
    trigger_type: str,
    actor=None,
    asset=None,
    scan_event=None,
    extra_context=None,
    workflow_definition_id: int | None = None,
    force_run: bool = False,
):
    base_context = {
        "asset": asset,
        "scan_event": scan_event,
        "trigger_type": trigger_type,
    }
    if extra_context:
        base_context.update(extra_context)

    workflow_defs = WorkflowDefinition.objects.filter(
        tenant_id=tenant_id,
        trigger_type=trigger_type,
        is_active=True,
    ).order_by("name")
    if workflow_definition_id:
        workflow_defs = workflow_defs.filter(id=workflow_definition_id)

    run_ids: list[int] = []
    for workflow in workflow_defs:
        if not force_run and not _entry_conditions_match(workflow.entry_conditions or {}, base_context):
            continue

        run = WorkflowRun.objects.create(
            tenant_id=tenant_id,
            workflow=workflow,
            asset=asset,
            scan_event=scan_event,
            status=WorkflowRun.RunStatus.RUNNING,
            context=_json_safe(base_context),
            input_data={"trigger_type": trigger_type},
            output_data={"executed_steps": []},
        )

        try:
            with track_workflow_execution(workflow.name):
                executed_steps = []
                for step in workflow.steps or []:
                    result = _execute_step(step, run, base_context, actor=actor)
                    executed_steps.append(result)

                run.output_data = {"executed_steps": executed_steps}
                run.status = WorkflowRun.RunStatus.SUCCESS
                run.completed_at = timezone.now()
                run.save(update_fields=["output_data", "status", "completed_at", "updated_at"])
                run_ids.append(run.id)
        except Exception as error:
            workflow_executions_total.labels(workflow_name=workflow.name, status='error').inc()
            run.status = WorkflowRun.RunStatus.FAILED
            run.output_data = {
                "error": str(error),
                "executed_steps": run.output_data.get("executed_steps", []),
            }
            run.completed_at = timezone.now()
            run.save(update_fields=["status", "output_data", "completed_at", "updated_at"])
            run_ids.append(run.id)

    return run_ids
