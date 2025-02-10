from utils.logger import *
import httpx


async def get_wealth_info(phone, message, type, stock):
    payload = {"phone": phone, "message": message, "type": type, "stock": stock}
    headers = {"Content-Type": "application/json"}
    logger.debug(payload)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://4ede-154-161-145-23.ngrok-free.app/api/chats",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            response_data = response.json()
            logger.debug(response_data)
            return response_data
        except Exception as error:
            raise error
