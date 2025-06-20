from flask import Flask, request
import requests
import os
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

VERIFY_TOKEN = "mybot123"
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("698497970011796")

scheduler = BackgroundScheduler()
scheduler.start()

# Store reminders as (chat_id, message, datetime) in memory
reminders = []

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent message response:", response.status_code, response.text)

def check_reminders():
    now = datetime.datetime.now().strftime("%H:%M")
    for r in reminders[:]:
        if r[2] == now:
            print(f"⏰ Sending reminder to {r[0]}: {r[1]}")
            send_whatsapp_message(r[0], f"⏰ Reminder: {r[1]}")
            reminders.remove(r)

scheduler.add_job(check_reminders, 'interval', minutes=1)

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Unauthorized", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("🔍 Incoming JSON:", data)  # Log the entire payload

    try:
        # Extract message
        entry = data.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])

        if not messages:
            print("⚠️ No messages in update.")
            return "OK", 200

        message = messages[0]
        text = message.get('text', {}).get('body', '').lower()
        from_number = message.get('from')

        print(f"📩 Received from {from_number}: {text}")

        if text.startswith("hi"):
            send_whatsapp_message(from_number, "Hi there! How can I help you today?")

        elif "remind me at" in text:
            parts = text.replace("remind me at", "").strip().split(" to ")
            if len(parts) == 2:
                time_part = parts[0].strip().replace("pm", "").replace("am", "").strip()
                task = parts[1].strip()
                try:
                    time_obj = datetime.datetime.strptime(time_part, "%H:%M")
                    formatted_time = time_obj.strftime("%H:%M")
                    reminders.append((from_number, task, formatted_time))
                    print(f"✅ Reminder scheduled at {formatted_time} for {from_number}: {task}")
                    send_whatsapp_message(from_number, f"✅ Reminder set at {formatted_time} to '{task}'")
                except ValueError:
                    send_whatsapp_message(from_number, "❌ Invalid time format. Use HH:MM in 24-hour format.")
            else:
                send_whatsapp_message(from_number, "❌ Could not parse reminder. Use: remind me at 18:30 to call mom")

        else:
            send_whatsapp_message(from_number, "❓ I didn’t understand that. Try: remind me at 14:00 to drink water")

    except Exception as e:
        print("🚨 Exception in webhook:", e)

    return "OK", 200

@app.route('/')
def home():
    return '✅ WhatsApp Reminder Bot is running!'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
