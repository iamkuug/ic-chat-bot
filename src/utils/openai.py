import asyncio
from openai import AsyncOpenAI as OpenAI
from utils.logger import *

gpt_client = OpenAI()


async def add_response_to_thread(thread_id: str, message: str):
    res = await gpt_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message,
    )

    return res 


async def get_chatgpt_response(thread_id: str, assistant_id: str) -> str:
    try:
        run = await gpt_client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id
        )

        max_attempts = 10
        base_delay = 1  # 1 second initial delay

        for attempt in range(max_attempts):
            run_status = await gpt_client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )

            if run_status.status == "completed":
                logger.info("Run status complete - Generated reply!")
                messages = await gpt_client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                return messages.data[0].content[0].text.value

            elif run_status.status == "failed":
                logger.error(
                    "Run execution failed - Reply couldn't be generated by model"
                )
                raise Exception("[Openai] Failed to generate response")

            elif run_status.status in ["queued", "in_progress"]:
                # Implement exponential backoff
                delay = base_delay * (2**attempt)
                logger.info(
                    f"Run in progress. Waiting {delay} seconds. Attempt {attempt + 1}"
                )
                await asyncio.sleep(delay)

            else:
                logger.warning(f"Unexpected run status: {run_status.status}")
                await asyncio.sleep(1)

        raise Exception("[Openai] Max retry attempts exceeded")

    except Exception as e:
        logger.error(f"Error in get_chatgpt_response: {e}")
        raise
