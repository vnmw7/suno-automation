from openai import OpenAI


def send_api_request(
    message: str,
):
    """This is an API for LLM chats."""

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
    )
    messages = [{"role": "user", "content": message}]
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model="google/gemma-3-27b-it:free",
        messages=messages,
    )
    return completion.choices[0].message.content


def get_verse_ranges(
    prompt: str,
):
    """
    Gets verse ranges.
    Example Output: ['1-10', '11-20', '21-31']
    """

    response = send_api_request(prompt)
    return response


def create_song_structure(
    prompt: str,
):
    """
    Gets verse ranges.
    Example Output: [Verse 1]:1-2,[Chorus]:3-5,[Verse 2]:6-8,[Bridge]:9-10
    """

    response = send_api_request(prompt)
    return response
