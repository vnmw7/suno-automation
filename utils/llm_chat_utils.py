import json
import os

import requests
from dotenv import load_dotenv  # type: ignore
from openai import OpenAI

load_dotenv()


def get_rate_limits():
    api_key = os.getenv("LLM_API_KEY")

    response = requests.get(
        url="https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {api_key}"},
    )

    print(json.dumps(response.json(), indent=2))


def send_api_request(
    message: str,
):
    """This is an API for LLM chats."""

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("LLM_API_KEY"),
    )
    messages = [{"role": "user", "content": message}]
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model="meta-llama/llama-3.3-8b-instruct:free",
        messages=messages,
    )
    return completion.choices[0].message.content


def llm_general_query(
    prompt: str,
):
    response = send_api_request(prompt)
    return response


get_rate_limits()
