from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from utils.mark_as_read import *
from utils.profiler import *
from utils.send_reply import *
from utils.check_env_status import *
from utils.logger import *
from utils.openai import *
from utils.wealth import *
from utils.standardize_phone import *
from constants import WEBHOOK_VERIFY_TOKEN, OPENAI_ASSISTANT_ID
from redis.asyncio import Redis
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()
check_env_status()


app = FastAPI()


redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    password=os.getenv("REDIS_PASSWORD", ""),
    username="default",
    db=0,
    decode_responses=True,
)


async def process_webhook_message(body: dict):
    try:
        message = (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("messages", [{}])[0]
        )

        if message.get("type") != "text":
            return

        logger.debug(f"Incoming webhook message: {message}")
        user_message = message["text"]["body"]
        sender_phone_number = message["from"]
        message_id = message["id"]

        number_is_blocked = await redis_client.sismember(
            "blocked-numbers", sender_phone_number
        )

        print(number_is_blocked)

        if number_is_blocked:
            logger.debug(
                f"User with number {sender_phone_number} is blocked, aborting ..."
            )
            return

        thread_key = f"thread:{sender_phone_number}"
        thread_id = await redis_client.get(thread_key)

        if not thread_id:
            thread = await gpt_client.beta.threads.create()
            thread_id = thread.id
            await redis_client.set(thread_key, thread_id)

        await add_response_to_thread(thread_id, user_message)
        gpt_reply = json.loads(
            await get_chatgpt_response(thread_id, OPENAI_ASSISTANT_ID)
        )

        message_type = gpt_reply.get("type")
        message_body = gpt_reply.get("message")
        stock = gpt_reply.get("stock")

        logger.debug(f"Incoming Message type: {message_type}")

        if message_type == "GENERAL":
            await send_reply(sender_phone_number, message_body, message_id)
            await mark_as_read(message_id)
        else:
            res = await get_wealth_info(
                sender_phone_number, message_body, message_type, stock, message_id
            )
            message_body = res.get("data").get("message")
            await send_reply(sender_phone_number, message_body, message_id)
            await mark_as_read(message_id)

    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")


@app.get("/")
async def health():
    try:
        await redis_client.ping()
        return JSONResponse(
            content={"status": "healthy", "redis": "connected"}, status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "redis": "not connected"}, status_code=500
        )


@app.post("/api/block")
async def block_number(request: Request):
    try:
        body = await request.json()
        phone = body.get("phone")

        if not phone:
            return JSONResponse(
                content={"message": "Field `phone` is required", "errors": []},
                status_code=400,
            )

        phone = standardize_phone_number(phone)

        not_blocked = await redis_client.sadd("blocked-numbers", phone)

        if not not_blocked:
            return JSONResponse(
                content={"message": "Phone number already blocked", "errors": []},
                status_code=200,
            )

        return JSONResponse(
            content={"message": "Phone number successfully added", "errors": []},
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            content={"message": f"Error processing request: {str(e)}", "errors": []},
            status_code=500,
        )


@app.post("/api/clear-cache")
async def clear_cache(request: Request):
    try:
        keys = await redis_client.keys(f"thread:*")

        if not keys:
            return JSONResponse(
                content={"message": "Cache is already empty"}, status_code=200
            )

        deleted = await redis_client.delete(*keys)

        return JSONResponse(
            content={"message": "Cache successfully cleared", "errors": []},
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(content=str(e), status_code=500)


@app.get("/webhook")
def verify_webhook(request: Request):
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
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()

        background_tasks.add_task(process_webhook_message, body)
        return JSONResponse(content="success", status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content=str(e), status_code=500)


if __name__ == "__main__":
    uvicorn.run(
        "app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True
    )
