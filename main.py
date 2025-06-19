from flask import Flask, request
import requests
import json
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 🛡️ Configurable Tokens
VERIFY_TOKEN = "mybot123"
ACCESS_TOKEN = "EAAUXJ8h1sSMBO1l2chzc4Uusencxe6R4sGefiLiaAqtbPJRFH9a3cpq8OXgLwdIlISYrboTPsK9dbn6L1jLy6LGUJOA4S6lsiILNuP4Ipd8ej6Cd2f7csfwV76Q2aIpmSZBMOPalcRKy7W8dKaKoXEajBZBulZA9qZCzWva3cJvZAJH59LIdpgmuVQS8WcpxS3gZDZD"
PHONE_NUMBER_ID = "698497970011796"
GROQ_API_KEY = "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"
GROQ_MODEL = "mixtral-8x7b-32768"

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()


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
    res = requests.post(url, headers=headers, json=data)
    print("📤 Sent message:", res.status_code, res.text)


def ask_groq_ai(message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant who understands reminders."},
            {"role": "user", "content": message}
        ]
    }
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified!")
            return challenge, 200
        else:
            return "Unauthorized", 403

    if request.method == "POST":
        data = request.get_json()
        print("📥 Incoming webhook:", json.dumps(data, indent=2))

        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            phone = message['from']
            text = message['text']['body']
            print(f"📨 Message from {phone}: {text}")

            if "remind" in text.lower():
                ai_reply = ask_groq_ai(f"Extract date/time and message from: {text}")
                send_whatsapp_message(f"✅ Reminder noted: {ai_reply}", phone)
                # Optional: Parse datetime & schedule actual reminder
            else:
                ai_response = ask_groq_ai(text)
                send_whatsapp_message(ai_response, phone)

        except Exception as e:
            print("❌ Error:", e)

        return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

