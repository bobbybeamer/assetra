import hashlib
import hmac
import json
import logging
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from celery import shared_task
from django.utils import timezone

from .models import BarcodeBatch, BarcodeLabel, WebhookDelivery, WebhookEndpoint
from .observability import (
    track_webhook_delivery,
    webhook_dead_letters_total,
    webhook_deliveries_total,
)
from .services import render_zpl

DEFAULT_MAX_WEBHOOK_ATTEMPTS = 5
DEFAULT_WEBHOOK_TIMEOUT_SECONDS = 10
DEFAULT_WEBHOOK_RETRY_BASE_SECONDS = 60


@shared_task
def generate_barcode_batch(batch_id: int) -> int:
    batch = BarcodeBatch.objects.select_related("template").get(pk=batch_id)
    template = batch.template
    created = 0
    for value in range(batch.start_sequence, batch.end_sequence + 1):
        code_value = f"{batch.prefix}{value}"
        zpl = ""
        if template and template.zpl_template:
            zpl = render_zpl(template.zpl_template, {"code": code_value})
        BarcodeLabel.objects.create(
            tenant=batch.tenant,
            batch=batch,
            code_value=code_value,
            zpl_payload=zpl,
            render_payload={"sequence": value},
        )
        created += 1
    return created


def _build_signature(secret: str, timestamp: str, payload_text: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), f"{timestamp}.{payload_text}".encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _next_retry_delay_seconds(attempt_count: int, base_seconds: int) -> int:
    return min(base_seconds * (2 ** max(attempt_count - 1, 0)), 3600)


@shared_task
def dispatch_webhook(
    endpoint_id: int,
    event_name: str,
    payload: dict,
    *,
    delivery_id: int | None = None,
    max_attempts: int = DEFAULT_MAX_WEBHOOK_ATTEMPTS,
    retry_base_seconds: int = DEFAULT_WEBHOOK_RETRY_BASE_SECONDS,
) -> int:
    endpoint = WebhookEndpoint.objects.get(pk=endpoint_id)

    delivery = (
        WebhookDelivery.objects.filter(id=delivery_id, endpoint=endpoint).first()
        if delivery_id
        else None
    )
    if not delivery:
        delivery = WebhookDelivery.objects.create(
            tenant=endpoint.tenant,
            endpoint=endpoint,
            event_name=event_name,
            payload=payload,
            status=WebhookDelivery.DeliveryStatus.PENDING,
        )

    with track_webhook_delivery(endpoint_id, delivery.id):
        delivery.attempt_count += 1
        now = timezone.now()
        payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        timestamp = str(int(now.timestamp()))

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AssetraWebhook/1.0",
            "X-Assetra-Event": event_name,
            "X-Assetra-Delivery-Id": str(delivery.id),
            "X-Assetra-Timestamp": timestamp,
        }
        if endpoint.secret:
            headers["X-Assetra-Signature"] = _build_signature(endpoint.secret, timestamp, payload_text)

        try:
            request = Request(endpoint.url, data=payload_text.encode("utf-8"), headers=headers, method="POST")
            with urlopen(request, timeout=DEFAULT_WEBHOOK_TIMEOUT_SECONDS) as response:
                response_code = response.status
                response_body = response.read().decode("utf-8")

            delivery.response_code = response_code
            delivery.response_body = response_body[:5000]

            if 200 <= response_code < 300:
                delivery.status = WebhookDelivery.DeliveryStatus.SUCCESS
                delivery.delivered_at = now
                delivery.next_attempt_at = None
                delivery.last_error = ""
                endpoint.last_delivery_at = now
                endpoint.save(update_fields=["last_delivery_at", "updated_at"])
                webhook_deliveries_total.labels(endpoint_id=str(endpoint_id), status='success').inc()
            else:
                raise RuntimeError(f"non-success webhook response: {response_code}")

        except (HTTPError, URLError, RuntimeError, Exception) as error:
            error_message = str(error)
            delivery.last_error = error_message
            if delivery.attempt_count < max_attempts and endpoint.is_active:
                delay = _next_retry_delay_seconds(delivery.attempt_count, retry_base_seconds)
                delivery.status = WebhookDelivery.DeliveryStatus.PENDING
                delivery.next_attempt_at = now + timedelta(seconds=delay)
                webhook_deliveries_total.labels(endpoint_id=str(endpoint_id), status='retry').inc()
                dispatch_webhook.apply_async(
                    kwargs={
                        "endpoint_id": endpoint.id,
                        "event_name": event_name,
                        "payload": payload,
                        "delivery_id": delivery.id,
                        "max_attempts": max_attempts,
                        "retry_base_seconds": retry_base_seconds,
                    },
                    countdown=delay,
                )
            else:
                delivery.status = WebhookDelivery.DeliveryStatus.DEAD_LETTER
                delivery.dead_lettered_at = now
                delivery.next_attempt_at = None
                webhook_deliveries_total.labels(endpoint_id=str(endpoint_id), status='dead_letter').inc()
                webhook_dead_letters_total.labels(endpoint_id=str(endpoint_id)).inc()

        delivery.save(
            update_fields=[
                "status",
                "response_code",
                "response_body",
                "attempt_count",
                "next_attempt_at",
                "last_error",
                "dead_lettered_at",
                "delivered_at",
                "updated_at",
            ]
        )
    return delivery.id
