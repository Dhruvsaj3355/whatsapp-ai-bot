from flask import Flask, request
import requests
import os
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

VERIFY_TOKEN = "mybot123"
ACCESS_TOKEN = os.getenv("EAAUXJ8h1sSMBO1l2chzc4Uusencxe6R4sGefiLiaAqtbPJRFH9a3cpq8OXgLwdIlISYrboTPsK9dbn6L1jLy6LGUJOA4S6lsiILNuP4Ipd8ej6Cd2f7csfwV76Q2aIpmSZBMOPalcRKy7W8dKaKoXEajBZBulZA9qZCzWva3cJvZAJH59LIdpgmuVQS8WcpxS3gZDZD")  # Set your token in environment
PHONE_NUMBER_ID = os.getenv("698497970011796")  # Set your phone ID in environment

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
    requests.post(url, headers=headers, json=payload)

def check_reminders():
    now = datetime.datetime.now().strftime("%H:%M")
    for r in reminders[:]:
        if r[2] == now:
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
    try:
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        text = message['text']['body'].lower()
        from_number = message['from']

        if text.startswith("hi"):
            send_whatsapp_message(from_number, "Hi there! How can I help you today?")

        elif "remind me at" in text:
            parts = text.replace("remind me at", "").strip().split(" to ")
            if len(parts) == 2:
                time_part = parts[0].strip().replace("pm", "").replace("am", "").strip()
                task = parts[1].strip()
                time_obj = datetime.datetime.strptime(time_part, "%H:%M")
                formatted_time = time_obj.strftime("%H:%M")
                reminders.append((from_number, task, formatted_time))
                send_whatsapp_message(from_number, f"✅ Reminder set at {formatted_time} to '{task}'")
            else:
                send_whatsapp_message(from_number, "Sorry, I couldn't understand that format. Use: remind me at 11:00 to eat")
        else:
            send_whatsapp_message(from_number, "Sorry, I didn't understand that. Can you rephrase?")
    except Exception as e:
        print("Error:", e)
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

