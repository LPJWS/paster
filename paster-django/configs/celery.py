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

app.conf.beat_schedule = {
    "daily_post": {
        "task": 'paster.tasks.daily_post',
        "schedule": crontab(hour='23',
                            minute=59,
                            )
    },
    'regular_post_3': {
        'task': 'paster.tasks.regular_post',
        'schedule': crontab(hour='3',
                            minute=0,
                            )
    },
    'regular_post_6': {
        'task': 'paster.tasks.regular_post',
        'schedule': crontab(hour='6',
                            minute=0,
                            )
    },
    'regular_post_9': {
        'task': 'paster.tasks.regular_post',
        'schedule': crontab(hour='9',
                            minute=0,
                            )
    },
    'regular_post_12': {
        'task': 'paster.tasks.regular_post',
        'schedule': crontab(hour='12',
                            minute=0,
                            )
    },
    'regular_post_15': {
        'task': 'paster.tasks.regular_post',
        'schedule': crontab(hour='15',
                            minute=0,
                            )
    },
    'regular_post_18': {
        'task': 'paster.tasks.regular_post',
        'schedule': crontab(hour='18',
                            minute=0,
                            )
    },
    'regular_post_21': {
        'task': 'paster.tasks.regular_post',
        'schedule': crontab(hour='21',
                            minute=0,
                            )
    },
}