from flask import Flask, request, Response
from utils.get_gpt_response import *
from utils.mark_as_read import *
from utils.send_reply import *
from utils.check_env_status import *
from utils.logger import *
from constants import WEBHOOK_VERIFY_TOKEN
from redis import Redis
from dotenv import load_dotenv
import json
import os

load_dotenv()
check_env_status()


app = Flask(__name__)

redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    password=os.getenv("REDIS_PASSWORD", ""),
    username="default",
    db=0,
    decode_responses=True,
)


@app.route("/", methods=["GET"])
def health():
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}, 200
    except Exception as e:
        return {"status": "unhealthy", "redis": str(e)}, 500


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return Response(challenge, status=200)
    else:
        logger.info("Webhook verification failed. Invalid token or mode.")
        return Response(status=403)


@app.post("/webhook")
def webhook():

    try:
        body = request.json
        message = (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("messages", [{}])[0]
        )

        if message.get("type") != "text":
            logger.info("No text found in webhook payload (ignore)")
            return Response({"msg": "No text found (ignore)"}, 200)

        logger.info("Incoming webhook message:")
        logger.info(message)

        user_message = message["text"]["body"]
        sender_phone_number = message["from"]
        message_id = message["id"]

        history_key = f"chat:history:{sender_phone_number}"
        conversation_json = redis_client.get(history_key)

        if conversation_json:
            messages_history = json.loads(conversation_json)
        else:
            messages_history = []

        messages_history.append({"role": "user", "content": user_message})

        gpt_reply = get_chatgpt_response(messages_history)

        messages_history.append({"role": "assistant", "content": gpt_reply})

        send_reply(sender_phone_number, gpt_reply, message_id)
        mark_as_read(message_id)

        redis_client.set(history_key, json.dumps(messages_history))

        return Response("success", 200)

    except Exception as e:
        logger.info(f"Error processing webhook: {str(e)}")
        return Response(str(e), 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT"))
