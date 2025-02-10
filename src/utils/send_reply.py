from constants import GRAPH_API_TOKEN, PHONE_NUMBER_ID
from utils.logger import *
import httpx


async def send_reply(to: str, reply: str, message_id: str) -> None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages",
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "text": {"body": reply},
                    "context": {"message_id": message_id},
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GRAPH_API_TOKEN}",
                },
            )
            response.raise_for_status()
            logger.debug(f"Sent reply to {to}: {reply}")
        except Exception as error:
            raise error
