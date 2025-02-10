import requests
from utils.logger import *


def get_wealth_info(phone, message, type, stock):

    payload = {"phone": phone, "message": message, "type": type, "stock": stock}
    headers = {"Content-Type": "application/json"}

    logger.debug(payload)

    try:
        
        response = requests.post(
            "https://4ede-154-161-145-23.ngrok-free.app/api/chats",
            json=payload,
            headers=headers,
        )

        response.raise_for_status()

        logger.debug(response.json())
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        raise
