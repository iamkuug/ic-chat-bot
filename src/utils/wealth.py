from utils.logger import *
from utils.send_reply import *
from constants import X_CHAT_KEY
import httpx


async def get_wealth_info(phone, message, type, stock, message_id):
    payload = {"phone": phone, "message": message, "type": type, "stock": stock}
    headers = {
        "Content-Type": "application/json",
        "X-CHAT-KEY": X_CHAT_KEY,
    }
    logger.debug(payload)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://dwmkwtwkabb76mra2cc4a3ragqpmaoet.staging.ic.africa/api/chats",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            response_data = response.json()
            logger.debug(response_data)
            return response_data
        except Exception as error:
            raise error
