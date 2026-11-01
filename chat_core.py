"""Core logic for the AI Chat Application (Gemini API).

Covers: environment variables, system/user/assistant messages, chat history,
model parameters, token usage, cost estimate, structured JSON output and
robust error handling.
"""
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELS = ["gemini-2.5-flash", "gemini-3.8-flash"]
DEFAULT_SYSTEM_PROMPT = "You are a helpful, friendly AI assistant. Keep answers clear and simple."

# Token optimisation: only the latest messages are sent with each request.
MAX_HISTORY = 10

# Approximate prices in USD per 1 million tokens. Update from the official
# Gemini pricing page; these numbers are only for a basic cost estimate.
PRICE_PER_1M = {"input": 0.30, "output": 2.50}


def get_client():
    """Create the API client using the key stored in the .env file."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")
    return genai.Client(api_key=api_key)


def to_contents(history, max_history=MAX_HISTORY):
    """Convert chat history (user/assistant messages) into Gemini contents.

    Gemini uses the role names 'user' and 'model', so 'assistant' is mapped to 'model'.
    """
    recent = history[-max_history:]
    return [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in recent
    ]


def estimate_cost(input_tokens, output_tokens):
    """Basic API cost estimate in USD."""
    return (
        input_tokens * PRICE_PER_1M["input"] + output_tokens * PRICE_PER_1M["output"]
    ) / 1_000_000


def friendly_error(error):
    """Turn raw API errors into short messages a user can understand."""
    msg = str(error)
    if "503" in msg:
        return "The model is busy right now. Please try again in a moment."
    if "429" in msg:
        return "Rate limit or free quota reached. Please wait a bit and try again."
    if "400" in msg and "API key" in msg:
        return "Your API key is not valid. Check GEMINI_API_KEY in the .env file."
    if "404" in msg:
        return "This model is not available for your key. Choose another model."
    if "403" in msg:
        return "Access denied. Check that your API key has permission."
    return f"Something went wrong: {msg}"


def chat(client, history, system_prompt=DEFAULT_SYSTEM_PROMPT, model=MODELS[0],
         temperature=0.7, max_tokens=1024, retries=3):
    """Send the chat history to the model and return the reply with usage details."""
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    last_error = None
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model, contents=to_contents(history), config=config
            )
            usage = response.usage_metadata
            in_tok = (usage.prompt_token_count or 0) if usage else 0
            out_tok = (usage.candidates_token_count or 0) if usage else 0
            text = response.text or "No text received. Try increasing 'Max output tokens'."
            return {
                "text": text,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cost": estimate_cost(in_tok, out_tok),
            }
        except Exception as e:  # noqa: BLE001
            last_error = e
            if "503" in str(e) or "429" in str(e):
                time.sleep(2 * (attempt + 1))  # wait, then retry
            else:
                break
    raise RuntimeError(friendly_error(last_error))


def summarize_chat_json(client, history, model=MODELS[0]):
    """Structured response: summarise the conversation as JSON."""
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in history[-MAX_HISTORY:])
    prompt = (
        "Summarize this conversation. Return ONLY valid JSON with keys: "
        "topic (string), key_points (list of strings), next_steps (list of strings).\n\n"
        + transcript
    )
    config = types.GenerateContentConfig(response_mime_type="application/json")
    try:
        response = client.models.generate_content(model=model, contents=prompt, config=config)
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise RuntimeError("The model did not return valid JSON. Please try again.")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(friendly_error(e))
