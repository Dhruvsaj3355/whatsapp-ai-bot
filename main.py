from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Replace with your actual details
VERIFY_TOKEN = "mybot123"
ACCESS_TOKEN = "EAAUXJ8h1sSMBO1l2chzc4Uusencxe6R4sGefiLiaAqtbPJRFH9a3cpq8OXgLwdIlISYrboTPsK9dbn6L1jLy6LGUJOA4S6lsiILNuP4Ipd8ej6Cd2f7csfwV76Q2aIpmSZBMOPalcRKy7W8dKaKoXEajBZBulZA9qZCzWva3cJvZAJH59LIdpgmuVQS8WcpxS3gZDZD"
PHONE_NUMBER_ID = "698497970011796"

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp AI Bot is live"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            messages = data['entry'][0]['changes'][0]['value']['messages']
            for message in messages:
                sender = message['from']  # user's phone number
                text = message['text']['body'] if 'text' in message else ''
                reply = generate_reply(text)
                send_message(sender, reply)
        except Exception as e:
            print("Webhook error:", e)
        return "OK", 200

def generate_reply(user_input):
    # Very simple bot logic for demo
    if user_input.lower() in ["hi", "hello"]:
        return "Hi there! How can I help you today?"
    elif "your name" in user_input.lower():
        return "I'm your friendly WhatsApp bot!"
    else:
        return "Sorry, I didn't understand that. Can you rephrase?"

def send_message(recipient, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": text}
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Send message response:", response.status_code, response.text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
