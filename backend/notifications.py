import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import models

def is_quiet_hours(settings):
    if not settings.quiet_hours_start or not settings.quiet_hours_end:
        return False
    
    now = datetime.now().strftime("%H:%M")
    start = settings.quiet_hours_start
    end = settings.quiet_hours_end
    
    if start < end:
        return start <= now <= end
    else: # Crosses midnight
        return now >= start or now <= end

def send_alert(log, settings):
    # Skip if quiet hours and not critical
    if is_quiet_hours(settings) and log.risk_level != 'CRITICAL':
        print("Quiet hours active. Skipping alert.")
        return

    message = f"[{log.risk_level}] {log.activity_type}: {log.description}"

    # 1. Webhook (Slack/Discord style)
    if settings.webhook_url:
        try:
            payload = {
                "text": message, 
                "username": "Sentinel AI", 
                "icon_emoji": ":shield:",
                "attachments": [{
                    "color": "#ff0000" if log.risk_level == "CRITICAL" else "#ffcc00",
                    "fields": [
                        {"title": "User", "value": log.user, "short": True},
                        {"title": "IP", "value": log.ip_address, "short": True},
                        {"title": "Details", "value": log.details}
                    ]
                }]
            }
            requests.post(settings.webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Webhook failed: {e}")

    # 2. Email (SMTP)
    if settings.email_notifications and settings.notification_email:
        if settings.smtp_server:
            try:
                msg = MIMEText(message)
                msg['Subject'] = f"Sentinel Alert - {log.risk_level}"
                msg['From'] = settings.smtp_username or "sentinel@example.com"
                msg['To'] = settings.notification_email
                
                server = smtplib.SMTP(settings.smtp_server, settings.smtp_port or 587)
                server.starttls()
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
                server.quit()
            except Exception as e:
                print(f"SMTP Email failed: {e}")
        else:
            # Fallback to mock/print if no SMTP server configured
            print(f"--- EMAIL ALERT TO {settings.notification_email} ---")
            print(f"Subject: Sentinel Alert - {log.risk_level}")
            print(message)
            print("------------------------------------------------")

    # 3. SMS (Twilio)
    if settings.sms_notifications and settings.twilio_account_sid and settings.twilio_auth_token:
        try:
            # Use requests to call Twilio API
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
            data = {
                "From": settings.twilio_from_number,
                "To": settings.twilio_to_number,
                "Body": message
            }
            # auth = (settings.twilio_account_sid, settings.twilio_auth_token)
            # requests.post(url, data=data, auth=auth)
            print(f"--- SMS ALERT (Simulated) TO {settings.twilio_to_number} ---")
            print(message)
        except Exception as e:
            print(f"SMS failed: {e}")

def test_notification(settings):
    results = {}
    
    # Webhook
    if settings.webhook_url:
        try:
            requests.post(settings.webhook_url, json={"text": "Test Notification from Sentinel AI"}, timeout=5)
            results["webhook"] = "success"
        except Exception as e:
            results["webhook"] = f"failed: {str(e)}"
    else:
        results["webhook"] = "skipped"
            
    # Email
    if settings.email_notifications:
        if settings.smtp_server:
            try:
                msg = MIMEText("Test Notification")
                msg['Subject'] = "Sentinel Test"
                msg['From'] = settings.smtp_username or "sentinel@example.com"
                msg['To'] = settings.notification_email
                
                server = smtplib.SMTP(settings.smtp_server, settings.smtp_port or 587)
                server.starttls()
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
                server.quit()
                results["email"] = "success"
            except Exception as e:
                results["email"] = f"failed: {str(e)}"
        else:
            results["email"] = "simulated_success"
    else:
        results["email"] = "skipped"

    # SMS
    if settings.sms_notifications:
         results["sms"] = "simulated_success"
    else:
         results["sms"] = "skipped"
         
    return results
