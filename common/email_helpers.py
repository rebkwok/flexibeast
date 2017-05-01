from django.conf import settings
from django.core.mail import send_mail
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template

from activitylog.models import ActivityLog

def send_support_email(e, module_name="", extra_subject=""):
    try:
        send_mail('{} An error occurred! ({})'.format(
                settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, extra_subject
            ),
            'An error occurred in {}\n\nThe exception '
            'raised was "{}"'.format(module_name, e),
            settings.DEFAULT_FROM_EMAIL,
            [settings.SUPPORT_EMAIL],
            fail_silently=True)
    except Exception as ex:
        ActivityLog.objects.create(
            log="Problem sending an email ({}: {})".format(
                module_name, ex
            )
        )
