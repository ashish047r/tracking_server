import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracking_project.settings")

app = Celery("tracking_project")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
