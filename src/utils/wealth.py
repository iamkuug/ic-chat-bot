from utils.logger import *
from utils.send_reply import *
import httpx


async def get_wealth_info(phone, message, type, stock, message_id):
    payload = {"phone": phone, "message": message, "type": type, "stock": stock}
    headers = {"Content-Type": "application/json"}
    logger.debug(payload)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://96c9-154-161-145-23.ngrok-free.app/api/chats",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            response_data = response.json()
            logger.debug(response_data)
            return response_data
        except Exception as error:
            # await send_reply(phone, "Sorry couldn't retreive info at this time", message_id)
            raise error
