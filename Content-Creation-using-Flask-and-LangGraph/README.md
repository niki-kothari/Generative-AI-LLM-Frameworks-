# Langgraph AI Demo Projects

This repository contains two AI demo workflows using Flask backends and Streamlit frontends.

## Project overview

1. **Content generation and evaluation**
   - `backend/content_creator_be.py`
   - `frontend/content_creator_fe.py`
   - Generates content for a requested topic using an LLM
   - Evaluates the generated content on language quality, examples/use cases, and advantages/limitations
   - Returns overall feedback and an average score

2. **Review sentiment analysis and response**
   - `backend/find_sentiment_be.py`
   - `frontend/find_sentiment_fe.py`
   - Detects whether a review is positive or negative
   - For positive reviews, generates a warm thank-you response
   - For negative reviews, diagnoses issue type, tone, and urgency, then generates an empathetic reply

## Requirements

- Python 3.10 or newer
- `pip`
- `Flask` and `Streamlit`
- `python-dotenv` and `pydantic`
- `requests`
- `langgraph` and `langchain-groq`

## Environment

The backend uses `ChatGroq` and expects a GROQ API key in `backend/.env`:

```ini
GROQ_API_KEY=your_api_key_here
```

## Install dependencies

From the project root:

```powershell
python -m pip install flask streamlit python-dotenv pydantic requests langgraph langchain-groq
```

## Run the content generation app

1. Start the backend server:

```powershell
python backend/content_creator_be.py
```

2. Start the Streamlit frontend:

```powershell
streamlit run frontend/content_creator_fe.py
```

3. In the browser, enter a topic and click `Generate and Evaluate`.

## Backend API endpoints

- `POST /generate`
  - Request body: `{ "topic": "..." }`
  - Response: `{ "content": "...", "feedback": "...", "score": ... }`

## Important notes

- Both frontends are hard-coded to call `http://127.0.0.1:5000`
- Start the backend before running the frontend UI
- Make sure the `.env` file is loaded and contains a valid `GROQ_API_KEY`

## Project structure

```text
backend/
  content_creator_be.py
  .env
frontend/
  content_creator_fe.py
README.md
```

