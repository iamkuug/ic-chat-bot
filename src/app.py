from flask import Flask, request, Response
from utils import get_gpt_response, mark_as_read, send_reply
from constants import WEBHOOK_VERIFY_TOKEN
import json

app = Flask(__name__)


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(challenge, status=200)
    else:
        print("Webhook verification failed. Invalid token or mode.")
        return Response(status=403)


@app.post("/webhook")
def webhook():
    print("Incoming webhook message:", json.dumps(request.json, indent=2))

    try:
        body = request.json
        message = (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("messages", [{}])[0]
        )

        if message.get("type") != "text":
            print("No text found in webhook payload")
            return

        user_message = message["text"]["body"]
        sender_phone_number = message["from"]
        message_id = message["id"]

        message_history = []

        gpt_reply = get_gpt_response(message_history)

        send_reply(sender_phone_number, gpt_reply, message_id)
        mark_as_read(message_id)

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return {"error": str(e)}, 500
