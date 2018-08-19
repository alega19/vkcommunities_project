from celery import Celery, signals


app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@signals.setup_logging.connect
def disable_default_logging_configuration(*args, **kwargs):
    pass
