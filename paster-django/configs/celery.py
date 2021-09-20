import os

from django.conf import settings
from celery import Celery
from celery.schedules import crontab


class CeleryConfig(object):
    broker_url = 'redis://redis-web-paster:6379/1'
    result_backend = 'redis://redis-web-paster:6379/1'
    redis_host = "redis-web"
    worker_send_task_events = True
    timezone = 'Europe/Moscow'
    worker_disable_rate_limits = True


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')

app = Celery('apps')
app.config_from_object(CeleryConfig)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
