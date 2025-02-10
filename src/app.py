from flask import Flask, request, Response, g
from utils.mark_as_read import *
from utils.profiler import *
from utils.send_reply import *
from utils.check_env_status import *
from utils.logger import *
from utils.openai import *
from utils.wealth import *
from constants import WEBHOOK_VERIFY_TOKEN, OPENAI_ASSISTANT_ID
from redis import Redis
from dotenv import load_dotenv
import time
import os

load_dotenv()
check_env_status()


app = Flask(__name__)


@app.before_request
def start_timer():
    """Store the start time before handling the request."""
    g.start_time = time.time()


@app.after_request
def log_request_time(response):
    """Calculate and log the request execution time after processing."""
    if hasattr(g, "start_time"):
        execution_time = time.time() - g.start_time
        logger.warning(f"Request to {request.path} took {execution_time:.4f} seconds")

    return response


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
        logger.debug("Webhook verified successfully!")
        return Response(challenge, status=200)
    else:
        logger.error("Webhook verification failed. Invalid token or mode.")
        return Response(status=403)


@app.post("/webhook")
def webhook():
    profiler = RequestProfiler()

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

        logger.debug(f"Incoming webhook message: {message}")

        user_message = message["text"]["body"]
        sender_phone_number = message["from"]
        message_id = message["id"]

        with profiler.measure("gpt_response"):
            thread_key = f"thread:{sender_phone_number}"
            thread_id = redis_client.get(thread_key)
            if not thread_id:
                thread = gpt_client.beta.threads.create()
                thread_id = thread.id
                redis_client.set(thread_key, thread_id)
            add_response_to_thread(thread_id, user_message)
            gpt_reply = json.loads(get_chatgpt_response(thread_id, OPENAI_ASSISTANT_ID))

        with profiler.measure("whatsapp_reply"):

            message_type = gpt_reply.get("type")
            message_body = gpt_reply.get("message")
            stock = gpt_reply.get("stock")

            print(gpt_reply)

            logger.debug(f"Incomming Message type: {message_type}")

            if message_type == "GENERAL":
                send_reply(sender_phone_number, message_body, message_id)
                mark_as_read(message_id)
            else:
                res = get_wealth_info(sender_phone_number, message_body, message_type, stock)
                message_body = res.get("data").get("message")

                send_reply(sender_phone_number, message_body, message_id)
                mark_as_read(message_id)

        profiler.report()

        return Response("success", 200)

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return Response(str(e), 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT"))
