from google.appengine.api import mail
from schedup.settings import EMAIL_ADDRESS


def send_email(subject, recipient, reply_to = None, on_behalf_of = None,
            bcc = None, body = None, html_body = None, files = {}):
    """Sends an email message

    Parameters (keyword arguments):
        sender
        subject
        recipient
        reply_to (optional)
        on_behalf_of (optional)
        bcc (optional)
        body (optional) - text-only email body
        html_body - HTML body
    """

    message = mail.EmailMessage(sender = EMAIL_ADDRESS, subject = subject)
    message.to = recipient

    if bcc:
        message.bcc = bcc
    if body:
        message.body = body
    if html_body:
        message.html = html_body
    if reply_to:
        message.reply_to = reply_to
    if on_behalf_of:
        message.headers = {'On-Behalf-Of': on_behalf_of }
    if files:
        message.attachments = files.items()
    
    message.send()





