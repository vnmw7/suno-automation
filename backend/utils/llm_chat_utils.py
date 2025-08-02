import json
import os
import re

import requests
from dotenv import load_dotenv  # type: ignore
from openai import APIError, OpenAI  # Import APIError

load_dotenv()


def get_rate_limits():
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("Error: LLM_API_KEY not found in environment variables.")
        return

    try:
        response = requests.get(
            url="https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("Rate limit info:")  # Added for clarity
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching rate limits: {e}")
    except json.JSONDecodeError:
        print(
            f"Error decoding rate limit JSON response: {response.text if response else 'No response'}"
        )


def extract_json_from_markdown(markdown_string: str):
    """
    Extracts a JSON object from a markdown string.
    """
    # Regex to find a JSON object within a markdown code block
    json_match = re.search(r"```json\n(.*?)\n```", markdown_string, re.DOTALL)
    if json_match:
        return json_match.group(1)
    return markdown_string


def send_api_request(
    message: str,
):
    """This is an API for LLM chats."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("Error: LLM_API_KEY not found for send_api_request.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    messages = [{"role": "user", "content": message}]

    print(
        "Sending request to LLM with model: deepseek/deepseek-r1-0528:free"
    )  # Corrected f-string

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "<YOUR_SITE_URL>"),
                "X-Title": os.getenv("OPENROUTER_SITE_NAME", "<YOUR_SITE_NAME>"),
            },
            extra_body={},
            model="deepseek/deepseek-r1-0528:free",
            messages=messages,
        )
        print(
            f"LLM API Response object: {completion}"
        )  # Log the entire completion object

        if completion and completion.choices and len(completion.choices) > 0:
            if completion.choices[0].message:
                return completion.choices[0].message.content
            else:
                print("Error: LLM API response choice does not contain a message.")
                print(
                    f"Choice object details: {completion.choices[0].model_dump_json(indent=2)}"
                )
                return None
        else:
            print(
                "Error: LLM API response does not contain choices or choices array is empty."
            )
            if completion:
                print(
                    f"Completion object details: {completion.model_dump_json(indent=2)}"
                )
            return None
    except APIError as e:
        print(f"OpenAI API Error: {e}")
        print(f"Status code: {e.status_code}")
        # Attempt to print response body if available
        if hasattr(e, "response") and e.response and hasattr(e.response, "text"):
            print(f"Response body: {e.response.text}")
        elif hasattr(e, "body") and e.body:  # For some versions/types of APIError
            print(f"Error Body: {e.body}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM API request: {e}")
        return None


def llm_general_query(
    prompt: str,
):
    # TODO: Add response caching to reduce API calls for identical prompts
    # TODO: Implement rate limiting handling with automatic retry
    # TODO: Add telemetry/metrics for API usage tracking
    response_content = send_api_request(prompt)
    if response_content is None:
        print(
            f"Failed to get response from LLM for prompt (first 100 chars): '{prompt[:100]}...'"
        )
    return response_content


if __name__ == "__main__":
    get_rate_limits()
