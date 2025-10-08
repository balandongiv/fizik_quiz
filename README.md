# Industrial Physics Quiz

This project implements a small Flask web application that delivers an Industrial Physics readiness quiz. The quiz is dynamically driven by the JSON configuration stored at `data/quiz_schema.json` and produces personalized feedback based on trait scores.

## Features

- JSON-driven quiz configuration with validation on load
- Dynamic question rendering with optional within-type shuffling
- Client-side progress indicator and persisted selections on validation errors
- Trait scoring with caps, overall Industrial Physics fit score, and tier mapping
- Tailored feedback, highlights, and recommended next steps
- Simple responsive UI with result visualizations

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the development server**

   ```bash
   python app.py
   ```

   The application listens on `http://127.0.0.1:8000` by default.

3. **Take the quiz**

   - Visit `/` for the introduction
   - Complete the quiz at `/quiz`
   - Review your personalized results at `/result`

## Project Structure

```
app.py               # Flask application entrypoint
quiz/                # Quiz domain modules (models, loader, scoring, forms, rendering, utils)
templates/           # Jinja2 templates for the UI
static/              # Stylesheet and client-side script
requirements.txt     # Python dependencies
```

## Configuration

Quiz content, scoring, and UI toggles are controlled via `data/quiz_schema.json`. Update this file to change questions, trait weights, or feedback messaging. The loader module performs validation to ensure trait codes and scoring data remain consistent.

## Environment Variables

- `APP_SECRET` — Overrides the default Flask secret key used for session management.
- `PORT` — Port number used when running `app.py` directly (defaults to `8000`).

## Testing Notes

The application relies on Flask's built-in development server. Manual validation steps are outlined in the project charter and can be followed by interacting with the running web app.
