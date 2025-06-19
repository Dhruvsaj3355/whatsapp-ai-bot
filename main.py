from flask import Flask, request
import requests
import json
import datetime
import threading
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

VERIFY_TOKEN = "mybot123"  # Change if needed
ACCESS_TOKEN = "EAAUXJ8h1sSMBOZCTcF9RlEkRHZApU2FDWPezDg2JPoejDRJ9aFWm9mfCViAVesMnaoNhLbbVFsM2IbZAl4jqHe1mByJXZBkzdRG0rJ5ZAhNu2H5yZCJ0t9hwLIHR2FhZAienKt65GMKQYZB7uyWTkKcHDSbiYQFyyd0brxwXZBLyH4HJMgKRUAp2wrKsy8K4uy0bxwZAA3C3gyQKR3ZBdWP22RU9mDrUn1tWerumkZBzOTQPfMh4SAZDZD"
PHONE_NUMBER_ID = "698497970011796"
GROQ_API_KEY = "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"

groq_model = "mixtral-8x7b-32768"

scheduler = BackgroundScheduler()
scheduler.start()
reminders = []


def send_whatsapp_message(text, to):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=data)


def ask_groq_ai(message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant who can also create reminders."},
            {"role": "user", "content": message}
        ]
    }
    response = requests.post(url, headers=headers, json=body)
    return response.json()['choices'][0]['message']['content']


def schedule_reminder(phone, message, when):
    def job():
        send_whatsapp_message(f"⏰ Reminder: {message}", phone)
    scheduler.add_job(job, 'date', run_date=when)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Unauthorized", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            phone = message['from']
            text = message['text']['body']

            if "remind" in text.lower():
                ai_reply = ask_groq_ai(f"Extract date/time and message: {text}")
                send_whatsapp_message(f"Reminder set: {ai_reply}", phone)
                # (Optional: Parse date using LLM output and schedule)
            else:
                reply = ask_groq_ai(text)
                send_whatsapp_message(reply, phone)
        except Exception as e:
            print("Error:", e)
        return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
