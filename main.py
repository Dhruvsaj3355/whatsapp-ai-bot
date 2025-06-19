from flask import Flask, request
import requests
import re
from datetime import datetime, timedelta
import threading
import os

app = Flask(__name__)

VERIFY_TOKEN = "mybot123"  # Your webhook verify token
ACCESS_TOKEN = "EAAUXJ8h1sSMBO1l2chzc4Uusencxe6R4sGefiLiaAqtbPJRFH9a3cpq8OXgLwdIlISYrboTPsK9dbn6L1jLy6LGUJOA4S6lsiILNuP4Ipd8ej6Cd2f7csfwV76Q2aIpmSZBMOPalcRKy7W8dKaKoXEajBZBulZA9qZCzWva3cJvZAJH59LIdpgmuVQS8WcpxS3gZDZD"  # Add your permanent or valid temporary token here
PHONE_NUMBER_ID = "698497970011796"  # Replace with your number ID


def send_whatsapp_message(message, phone_number_id, to_number, access_token):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    response = requests.post(url, headers=headers, json=data)
    print("Sent message response:", response.text)


def parse_reminder(message):
    match = re.match(r'remind me at (\d{1,2}:\d{2})(?: ?(am|pm)?)? to (.+)', message, re.IGNORECASE)
    if not match:
        return None
    time_str, am_pm, task = match.groups()
    now = datetime.now()

    try:
        time_obj = datetime.strptime(time_str.strip(), "%H:%M")
    except ValueError:
        return None

    if am_pm:
        if am_pm.lower() == 'pm' and time_obj.hour < 12:
            hour = time_obj.hour + 12
        elif am_pm.lower() == 'am' and time_obj.hour == 12:
            hour = 0
        else:
            hour = time_obj.hour
    else:
        hour = time_obj.hour

    reminder_time = now.replace(hour=hour, minute=time_obj.minute, second=0, microsecond=0)
    if reminder_time < now:
        reminder_time += timedelta(days=1)

    delay = (reminder_time - now).total_seconds()
    return delay, task


def schedule_reminder(delay, task, phone_number_id, from_number, access_token):
    def send():
        send_whatsapp_message(f"⏰ Reminder: {task}", phone_number_id, from_number, access_token)
    threading.Timer(delay, send).start()


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        print("Received:", data)

        try:
            messages = data['entry'][0]['changes'][0]['value']['messages']
            if messages:
                message = messages[0]
                text = message['text']['body']
                from_number = message['from']

                parsed = parse_reminder(text)
                if parsed:
                    delay, task = parsed
                    schedule_reminder(delay, task, PHONE_NUMBER_ID, from_number, ACCESS_TOKEN)
                    send_whatsapp_message(f"Got it! I will remind you to: {task}", PHONE_NUMBER_ID, from_number, ACCESS_TOKEN)
                elif text.lower() == "hi":
                    send_whatsapp_message("Hi there! How can I help you today?", PHONE_NUMBER_ID, from_number, ACCESS_TOKEN)
                else:
                    send_whatsapp_message("Sorry, I didn't understand that. Try something like 'remind me at 10:30 to call mom'", PHONE_NUMBER_ID, from_number, ACCESS_TOKEN)

        except Exception as e:
            print("Error:", e)

        return "OK", 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
