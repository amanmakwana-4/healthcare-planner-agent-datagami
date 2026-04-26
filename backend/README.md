# Backend - Healthcare Planning Assistant

This backend runs a CrewAI workflow that generates a concise healthcare plan from:
- A disease or symptom topic
- A city/location input

It combines:
- Medical research from web search
- Nearby hospitals from OpenStreetMap/Overpass
- Nearby doctors/clinics from OpenStreetMap/Overpass

## Tech Stack

- Python
- CrewAI
- LangChain Groq (LLM)
- DuckDuckGo Search (ddgs)
- OpenStreetMap APIs (Nominatim + Overpass)

## Project Files

- `main.py`: CLI entry point
- `crew_setup.py`: Crew orchestration
- `tasks.py`: Task definitions and expected outputs
- `agents.py`: Agent setup and custom tools
- `requirements.txt`: Python dependencies
- `.env`: Local secrets (not committed)

## Prerequisites

- Python 3.10+
- A Groq API key
- Internet access (for search + map APIs)

## Environment Variables

Create `backend/.env` with:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Do not commit `.env`.

## Installation

From the backend folder:

```bash
pip install -r requirements.txt
```

## Run

From the backend folder:

```bash
python main.py
```

### Run as API (for frontend integration)

From the backend folder:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

API endpoints:

- `GET /health`
- `POST /generate-plan` with JSON body:

```json
{
	"topic": "diabetes",
	"location": "Ujjain"
}
```

You will be prompted for:
- Disease or symptoms
- City/location

The program then runs a sequential Crew pipeline and prints a final concise healthcare plan.

## How It Works

1. `research_task` gathers condition summary, symptoms, treatments, and specialist guidance.
2. `hospital_task` calls `hospital_search` to fetch real nearby hospitals.
3. `doctor_task` calls `doctor_search` to fetch nearby doctors/clinics.
4. `schedule_task` composes a short structured final plan.

## Output Notes

- Final output is intentionally trimmed for readability.
- Tool-based tasks are instructed not to invent hospital/doctor names.
- If map data is limited, fallback web search is used to return practical options.

## Troubleshooting

- Missing API key:
	- Ensure `GROQ_API_KEY` exists in `backend/.env`.
- Rate limit errors:
	- `main.py` retries automatically with backoff.
- No hospitals/doctors found:
	- Try a clearer location format (for example: `City, State, Country`).
- Dependency issues:
	- Reinstall with `pip install -r requirements.txt`.

## Security

- Rotate any key that was previously exposed.
- Keep all secrets in `.env` only.
- Never hardcode credentials in source files.
