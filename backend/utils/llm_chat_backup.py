import os

from dotenv import load_dotenv  # type: ignore
from openai import APIError, OpenAI  # Import APIError

load_dotenv()


def send_api_request(
    message: str,
):
    """This is an API for LLM chats."""
    api_key = os.getenv("AIMLAPI_KEY")  # Changed to AIMLAPI_KEY
    if not api_key:
        print(
            "Error: AIMLAPI_KEY not found for send_api_request."
        )  # Updated error message
        return None

    client = OpenAI(
        base_url="https://api.aimlapi.com/v1",  # Changed to AIMLAPI base_url
        api_key=api_key,
    )
    messages = [{"role": "user", "content": message}]

    print("Sending request to LLM with model: gpt-4o")

    try:
        completion = client.chat.completions.create(
            model="google/gemma-2-27b-it",  # Changed to gpt-4o
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


def aimlapi_general_query(
    prompt: str,
):
    response_content = send_api_request(prompt)
    if response_content is None:
        print(
            f"Failed to get response from LLM for prompt (first 100 chars): '{prompt[:100]}...'"
        )
    return response_content


if __name__ == "__main__":
    print("\nTesting llm_general_query:")
    test_prompt = "Tell me a short joke."
    test_response = aimlapi_general_query(test_prompt)
    if test_response:
        print(f"Response for '{test_prompt}': {test_response}")
    else:
        print(f"No response for '{test_prompt}'")
