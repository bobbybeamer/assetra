import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assetra_platform.settings")

app = Celery("assetra_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
