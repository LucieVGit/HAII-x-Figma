# UXmethod — canonical Streamlit app

Streamlit is the canonical UXmethod interface. The React/Figma files are visual reference only.
Gemini runs server-side through `streamlit_app/ai.py`; API keys never reach the browser or Git.

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
Configure `GEMINI_API_KEY` or `GOOGLE_API_KEY` in Streamlit secrets. Do not put keys in frontend
code, `.env` files committed to Git, or the repository. On Streamlit Community Cloud, add
`GEMINI_API_KEY` in the app's **Secrets** settings.

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
- **Ideation → Brainstorming prompt bank**: generates 6 prompts from the complete project context.
  Clicking a prompt adds it to the brainstorming notebook.
- **Ideation → Idea landscape**: places every brainstorming idea on a visual map and labels its
  dimension for quick review.

Notes last for one browser session. Use **Download notes (.md)** in the sidebar to keep a copy.
