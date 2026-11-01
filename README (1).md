# AI Chat Application

Module 3 project of the Generative AI Virtual Internship at **Codomax Digital Solutions**.

**Author:** Tarun Upadhyay

A chat application built with Python, the Gemini API and Streamlit. It remembers the conversation, supports custom instructions and shows token usage and an estimated cost.

## Features
| Requirement | Where it is done |
|---|---|
| LLM API connection with Python | `chat_core.py` (`genai.Client`) |
| Authentication and environment variables | API key loaded from `.env` with `python-dotenv` |
| System / user / assistant messages | `to_contents()` maps chat history to model roles |
| Chat history | Streamlit `session_state`, last 10 messages sent each time |
| Custom instructions | Sidebar text box (system prompt) |
| Model parameters | Temperature and max output tokens sliders, model selector |
| Token usage | Input and output tokens shown in the sidebar |
| Basic API cost management | Cost estimate + history trimming to save tokens |
| Structured responses | "Summarize chat (JSON)" button returns topic, key points, next steps |
| Robust error handling | Retry for 503/429 and friendly error messages |
| Basic UI | Streamlit chat interface |

## Project structure
```
.
├── app.py             # Streamlit user interface
├── chat_core.py       # API calls, history, tokens, cost, errors
├── requirements.txt
└── README.md
```

## Setup
1. Install packages:
   ```
   pip install -r requirements.txt
   ```
2. Create a file named `.env` in the project folder (never upload this file to GitHub):
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. Run the app:
   ```
   streamlit run app.py
   ```

## How it works
```
User message -> chat history -> (system prompt + last 10 messages) -> Gemini API -> reply
                                                              |-> tokens + cost shown in sidebar
```

## Cost management
- Only the latest 10 messages are sent, so long chats do not keep growing the token count.
- Max output tokens limits the reply length.
- Prices in `chat_core.py` are approximate; update them from the official pricing page.

## Screenshots
Add 1-2 screenshots of the running app here.

## Key learnings
- LLMs have no memory, so the full recent history must be sent with every request.
- A system prompt controls the assistant's behaviour and tone.
- Tokens decide both cost and context limits.
- Good error handling makes an app reliable when the API is busy.
- API keys belong in `.env`, never in code or on GitHub.
