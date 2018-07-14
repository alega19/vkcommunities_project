from smtplib import SMTPException

from django.core.mail import send_mail as sync_send_mail
from celery.utils.log import get_task_logger

from config.celery import app, task_msg


logger = get_task_logger(__name__)


@app.task(bind=True, autoretry_for=(SMTPException,), default_retry_delay=10, max_retries=2)
def send_mail(self, subject, message, from_email, recipient_list, **kwargs):
    logger.info(task_msg(self, 'an email to {}'.format(', '.join(recipient_list))))
    sync_send_mail(subject, message, from_email, recipient_list, **kwargs)
