from google.appengine.api import mail as _mail
from schedup.settings import EMAIL_ADDRESS


def send_email(subject, to, body):
    _mail.send_mail(sender = EMAIL_ADDRESS, to = to, subject = subject, body = body)


