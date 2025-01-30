from constants import SYSTEM_PROMPT, OPENAI_API_KEY
from utils.logger import *
import requests


# @Depracated
def get_chatgpt_response(messages: list[str]) -> str:
    try:
        full_messages = [SYSTEM_PROMPT] + messages

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": full_messages,
                "max_tokens": 150,
                "temperature": 0.7,
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            },
        )

        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
        return reply

    except requests.exceptions.RequestException as error:
        error_message = (
            error.response.json() if hasattr(error, "response") else str(error)
        )
        logger.error(f"Error communicating with OpenAI: {error_message}")
        return "Sorry, I am unable to process your request at the moment."
