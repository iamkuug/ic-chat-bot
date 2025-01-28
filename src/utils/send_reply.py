from constants import GRAPH_API_TOKEN, PHONE_NUMBER_ID
import requests


def send_reply(to: str, reply: str, message_id: str) -> None:
    try:
        response = requests.post(
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
        print(f"Sent reply to {to}: {reply}")

    except requests.exceptions.RequestException as error:
        error_message = (
            error.response.json() if hasattr(error, "response") else str(error)
        )
        print(f"Error sending message via WhatsApp API: {error_message}")
