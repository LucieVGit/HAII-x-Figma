# UXmethod — Streamlit version

A Python/Streamlit port of the UXmethod design in `src/App.tsx`. Gemini is called from the
server, so your API key is never sent to the browser.

## Setup

```bash
cd streamlit_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
For Windows

```bash
cd streamlit_app
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```
The app reads the API key from the `.env` file at the repo root, which is shared with the React app.
Any of these variable names work: `GEMINI_API_KEY`, `GOOGLE_API_KEY`, or `VITE_GEMINI_API_KEY`.
When you deploy to Streamlit Community Cloud, put `GEMINI_API_KEY` in the app's **Secrets** instead.

The model can be changed with `GEMINI_MODEL`. It defaults to `gemini-3.8-flash`.

## Run

```bash
cd streamlit_app
source .venv/bin/activate
streamlit run app.py
```
For Windows

```bash
cd streamlit_app
.venv\Scripts\activate.bat
streamlit run app.py
```

Run it from inside `streamlit_app/` so the theme in `.streamlit/config.toml` is loaded.

## Where Gemini is used

- **AI coach → "Review with AI coach"**: reads the notebook for the current phase and returns 3 ranked
  suggestions (add / reframe / consider). You can apply, comment on, or dismiss each one.
- **Ideation → Brainstorming prompt bank**: generates 6 prompts from your notebook. Clicking a prompt
  adds it to the notebook. If there's no key, or the call fails, it falls back to local template prompts.

Notes last for one browser session. Use **Download notes (.md)** in the sidebar to keep a copy.
