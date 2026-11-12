# UXmethod

UXmethod is a Streamlit application that helps a UX team move from an open
question to grounded ideas. It follows the first three phases of the book-based
methodology:

1. **Planning**: project definition, secondary research, recruitment, and
   ethics.
2. **Exploration**: interviews, focus groups, observation, surveys, and
   cultural probes.
3. **Ideation**: brainstorming, ideation cards, design studio, experience maps,
   personas, and generative techniques.

The Streamlit application is the canonical interface. The React/Figma files in
`src/` are visual reference code and are not the production Gemini integration.

## Architecture

The application has two main Python modules:

- `app.py`: Streamlit entry point, UI rendering, UX methodology content,
  session state, callbacks, notebook editing, suggestions, and Markdown export.
- `ai.py`: Gemini client configuration, prompts, model fallback, response
  parsing, and AI-specific fallbacks.

The application is server-side:

```text
Browser
  -> Streamlit app (app.py)
      -> Gemini client (ai.py)
          -> Gemini API
```

The Gemini API key is never intentionally sent to the browser. The browser
communicates with Streamlit, and Streamlit calls Gemini.

## Installation and configuration

### Windows

```powershell
cd streamlit_app
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS/Linux

```bash
cd streamlit_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For local development, create an ignored `.env` file at the repository root.
The application accepts these API-key names, in this order:

1. `GEMINI_API_KEY`
2. `GOOGLE_API_KEY`
3. `VITE_GEMINI_API_KEY`
4. `VITE_GOOGLE_API_KEY`

Streamlit Secrets can provide `GEMINI_API_KEY` or `GOOGLE_API_KEY` instead.
Never commit a key or put it in frontend code.

The model can be configured with:

```dotenv
GEMINI_MODEL=gemini-3.8-flash
```

If no model variable is set, the default is `gemini-3.8-flash`. The fallback
models configured in `ai.py` are `gemini-3.7-flash`, `gemini-3.5-flash`, and
`gemini-3.5-flash-lite`. The client is cached with Streamlit
`@st.cache_resource` and uses a 20-second HTTP timeout.

## Main user features

### Project overview

The overview lets the user name a project and choose one of the three
methodology phases. The project name is kept in Streamlit session state and is
shown in the header.

### Method notebooks

Each of the 15 methods has its own notebook. Text is edited in a `st.text_area`
except brainstorming method 9, which accepts one idea at a time through a
`st.text_input`.

Notebook content is held in:

```python
st.session_state.notebooks
```

The notebook is the main input sent to Gemini. For a phase review, only the
current method's notebook is sent. For project-wide ideation features, the
completed project context combines the relevant notebooks and labels each
section with its method code and title.

### AI coach

The **Review with AI coach** button calls
`generate_coach_suggestions()` with:

- the current phase;
- the phase methods;
- the methodology rationale;
- the current notebook text.

Gemini is instructed to return three ranked suggestions:

- `add`: something missing;
- `remove`: something to reframe, remove, or correct;
- `consider`: an open question for the team.

Each suggestion is expected to contain:

```json
{
  "type": "add",
  "importance": "high",
  "label": "Success criteria",
  "text": "Suggestion text",
  "action": "Add criteria",
  "applyText": "Text that can be appended to the notebook"
}
```

The UI lets the user apply, dismiss, or comment on a suggestion. Applying an
`add` or `remove` suggestion appends its `applyText` to the notebook. A
`consider` suggestion opens a team-note dialog instead.

### Brainstorming prompt bank

On method 9, the prompt bank sends the completed project context to Gemini and
requests six short prompts. This response is plain text, one prompt per line.
The parser:

1. splits the response into lines;
2. removes bullets and numbering;
3. removes lines shorter than 13 characters;
4. keeps at most six prompts.

Clicking a prompt appends it to the brainstorming notebook.

### Idea landscape

The brainstorming notebook is converted into one idea per non-empty line.
Bullets and numeric prefixes are removed. Gemini is asked to return an object
like:

```json
{
  "ideas": [
    {
      "id": 1,
      "dimension": "Promising direction",
      "x": 35,
      "y": 70
    }
  ]
}
```

`x` and `y` are clamped locally to the range 0–100. If Gemini is unavailable,
returns an unusable response, or raises an exception, deterministic local
coordinates and the label `Needs review` are used.

### Export

The sidebar provides **Download notes (.md)**. The generated Markdown includes
all methodology notebooks and team notes. It is the only persistent export
provided by the application.

## Gemini request and response handling

The common `call_gemini()` function calls the Google GenAI SDK:

```python
client.models.generate_content(
    model=model,
    contents=prompt,
    config=config,
)
```

For the coach and idea landscape, the configuration currently sets:

```python
response_mime_type="application/json"
```

This requests JSON, but it is **not strict Structured Output**. The current
code does not provide `response_json_schema`, Pydantic models, or a JSON Schema.
The expected structure is described in the natural-language prompt and then
parsed locally with `json.loads()`.

Consequently:

- the model is not aware of Python's parser or UI types;
- the prompt describes the expected keys and values;
- `json.loads()` checks JSON syntax;
- Python code performs only partial shape and value validation;
- malformed or unexpected responses can still occur.

The application does not currently use Gemini tool/function calling. Tool
calling would be a separate mechanism for having Gemini request an explicit
server-side function. It is not required for the current coach, prompt-bank,
or idea-landscape output.

For stricter guarantees, the coach and idea-landscape calls should use
`response_json_schema` and local typed validation. Local validation should
still remain in place because API output must never be trusted blindly.

## State, persistence, and logging

The application stores state in `st.session_state`, including:

- `notebooks`;
- `notes`;
- `suggestions`;
- `accepted`;
- `ai_prompts`;
- `coach_status`;
- `prompt_status`;
- `last_model`;
- project name and navigation state.

This is session state, not a database. Notes, prompts, suggestions, and model
selection are lost when the Streamlit session ends unless the user downloads
the Markdown export.

The application does not explicitly log Gemini prompts, raw responses, or
notebook contents. Gemini responses are parsed and transformed in memory.
Streamlit and the underlying SDK may still produce their own runtime or
network logs outside the application code.

Errors are intended to be converted into a short status message for the UI.
The coach error branch in `app.py` currently calls `_short_error`, while the
imported helper in `ai.py` is named `short_error`; this should be corrected if
that error path needs to be relied on.

## Model fallback behavior

`call_gemini()` tries the last successful model first, followed by the
configured primary model and the fallback models. The selected model is stored
in `st.session_state.last_model`.

HTTP/API errors with codes 400, 401, or 403 are raised immediately. Other
errors cause the next candidate model to be tried. If every candidate fails,
the last error is raised.

## Security and privacy considerations

- Keep API keys in ignored `.env` files or Streamlit Secrets.
- Do not put Gemini keys in `src/` or other browser-delivered code.
- Notebook contents and project context are sent to Gemini when an AI feature
  is invoked.
- The application has no explicit redaction or anonymization layer.
- Do not enter confidential or personal information unless the deployment and
  data-processing requirements have been reviewed.

## Code navigation

- Start the application in `streamlit_app/app.py` with `main()`.
- Inspect `init_state()` for session-state initialization.
- Inspect `render_sidebar()`, `render_overview()`, and
  `render_notebook()` for the main UI.
- Inspect `render_coach()` for the coach interaction and suggestion actions.
- Inspect `render_prompt_bank()` and `render_idea_landscape()` for ideation.
- Inspect `ai.py` for all Gemini calls and response parsing.
- Inspect `notes_markdown()` for the export format.

## Dependencies

The application uses:

- `streamlit` for the UI and session state;
- `google-genai` for the Gemini API;
- `python-dotenv` for loading the root `.env` file.
