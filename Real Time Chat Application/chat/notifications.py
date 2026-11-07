"""
Email Notification Service for DjangoChat
Handles automated email alerts to offline registered users via Gmail SMTP (or Console backend).
"""

import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def _send_email_worker(subject, plain_text, html_content, to_email):
    """
    Worker function executed in a background daemon thread to send an email without blocking.
    """
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'djangochat.notifications@gmail.com')
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        print(f"[DjangoChat Email] -> Notification email successfully sent to {to_email}", flush=True)
        logger.info(f"[DjangoChat Email] Successfully sent notification to {to_email}")
    except Exception as exc:
        print(f"[DjangoChat Email ERROR] -> Failed sending to {to_email}: {exc}", flush=True)
        logger.warning(f"[DjangoChat Email] Could not send email notification to {to_email}: {exc}")


def send_offline_email(recipient, sender, message_content, chat_type='private', group_name=None, has_attachment=False):
    """
    Sends an email notification to recipient if and only if:
    1. Recipient is not the sender
    2. Recipient has an email address registered
    3. Recipient is currently OFFLINE (profile.is_online == False)
    4. Recipient has email notifications enabled (profile.email_notifications == True)
    """
    if not recipient or recipient == sender:
        return False

    if not recipient.email or not recipient.email.strip():
        return False

    # Check recipient profile
    profile = getattr(recipient, 'profile', None)
    if not profile:
        return False

    # Only send notification when user is OFFLINE
    if profile.is_online:
        return False

    # Check if user opted in for email notifications
    if not profile.email_notifications:
        return False

    sender_name = sender.get_full_name() or sender.username
    recipient_name = recipient.get_full_name() or recipient.username
    current_time_str = timezone.localtime(timezone.now()).strftime('%d %b %Y, %I:%M %p')

    # Truncate preview if very long
    preview = message_content.strip()
    if len(preview) > 280:
        preview = preview[:280] + "..."

    if has_attachment and not preview:
        preview = "[File/Image Attachment]"

    if chat_type == 'group' and group_name:
        subject = f"[DjangoChat] New message in '{group_name}' from {sender_name}"
        location_title = f"Group: {group_name}"
    else:
        subject = f"[DjangoChat] New direct message from {sender_name}"
        location_title = f"Direct Message from {sender_name}"

    # Plain text content
    plain_text = f"""Hello {recipient_name},

You have received a new message on DjangoChat while you were offline.

From: {sender_name}
Chat: {location_title}
Time: {current_time_str}

Message:
"{preview}"

Log in to your DjangoChat account to reply to this message.
Thank you for using DjangoChat!
"""

    # Rich HTML content with modern email template styling
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 24px; color: #1e293b; }}
    .card {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
    .header {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 24px 30px; color: #ffffff; }}
    .header h2 {{ margin: 0; font-size: 20px; font-weight: 700; display: flex; align-items: center; gap: 8px; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
    .body {{ padding: 28px 30px; }}
    .greeting {{ font-size: 16px; font-weight: 600; margin-bottom: 12px; }}
    .notice {{ color: #64748b; font-size: 14px; margin-bottom: 20px; line-height: 1.5; }}
    .message-box {{ background-color: #f8fafc; border-left: 4px solid #4f46e5; padding: 16px; border-radius: 6px; margin-bottom: 24px; }}
    .sender-tag {{ font-size: 12px; font-weight: 700; color: #4f46e5; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
    .message-text {{ font-size: 15px; color: #0f172a; margin: 0; white-space: pre-wrap; font-style: italic; }}
    .meta {{ font-size: 12px; color: #94a3b8; margin-top: 8px; }}
    .btn-wrap {{ text-align: center; margin: 28px 0 16px; }}
    .btn {{ display: inline-block; background: #4f46e5; color: #ffffff !important; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: 600; font-size: 14px; box-shadow: 0 2px 6px rgba(79,70,229,0.3); }}
    .footer {{ background-color: #f8fafc; padding: 18px 30px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; }}
    .badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 11px; background: #e0e7ff; color: #3730a3; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>DjangoChat Notification</h2>
      <p>Offline Message Alert &bull; MCA Academic Project</p>
    </div>
    <div class="body">
      <div class="greeting">Hello {recipient_name},</div>
      <p class="notice">
        You were <strong>offline</strong> when you received a new message from <strong>{sender_name}</strong> in <strong>{location_title}</strong>.
      </p>

      <div class="message-box">
        <div class="sender-tag">{sender_name} &bull; <span class="badge">{location_title}</span></div>
        <p class="message-text">"{preview}"</p>
        <div class="meta">Sent on {current_time_str} (IST)</div>
      </div>

      <div class="btn-wrap">
        <a href="http://127.0.0.1:8000/chat/" class="btn">Open DjangoChat to Reply</a>
      </div>

      <p class="notice" style="font-size: 12px; text-align: center; margin-bottom: 0;">
        You received this email because offline notifications are enabled in your DjangoChat profile.
      </p>
    </div>
    <div class="footer">
      DjangoChat &copy; 2026 &bull; Real-Time Chat Application with WebSockets & SQLite
    </div>
  </div>
</body>
</html>
"""

    # Spawn daemon thread so WebSocket message sending is completely non-blocking
    thread = threading.Thread(
        target=_send_email_worker,
        args=(subject, plain_text, html_content, recipient.email.strip()),
        daemon=True
    )
    thread.start()
    return True


def notify_offline_private_recipient(conversation, sender, message_content, has_attachment=False):
    """
    Checks the other participant of the conversation, and if offline, sends an email notification.
    """
    try:
        recipient = conversation.get_other_user(sender)
        return send_offline_email(
            recipient=recipient,
            sender=sender,
            message_content=message_content,
            chat_type='private',
            has_attachment=has_attachment
        )
    except Exception as exc:
        logger.warning(f"[DjangoChat] Error in notify_offline_private_recipient: {exc}")
        return False


def notify_offline_group_members(group, sender, message_content, has_attachment=False):
    """
    Finds all members of the group (excluding sender) who are offline and have email notifications on,
    and sends them email alerts.
    """
    try:
        offline_members = group.members.exclude(id=sender.id).filter(
            profile__is_online=False,
            profile__email_notifications=True
        ).exclude(email='')

        count = 0
        for member in offline_members:
            send_offline_email(
                recipient=member,
                sender=sender,
                message_content=message_content,
                chat_type='group',
                group_name=group.name,
                has_attachment=has_attachment
            )
            count += 1
        return count
    except Exception as exc:
        logger.warning(f"[DjangoChat] Error in notify_offline_group_members: {exc}")
        return 0

