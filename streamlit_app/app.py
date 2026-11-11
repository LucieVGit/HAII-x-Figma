"""UXmethod — Streamlit port of the Figma Make design (src/App.tsx).

Gemini is called server-side, so the API key never reaches the browser.
Run from this folder:  streamlit run app.py
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
PUBLIC = ROOT / "public"
LOGO = PUBLIC / "uxmethod-logo.png"
SCOPE_IMG = PUBLIC / "methodology-scope.png"

load_dotenv(ROOT / ".env")
load_dotenv(APP_DIR / ".env")


def _get_api_key() -> str | None:
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "VITE_GEMINI_API_KEY", "VITE_GOOGLE_API_KEY"):
        value = os.getenv(name)
        if value and value.strip() and value.strip() != "your-api-key-here":
            return value.strip()
    try:
        return st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        return None


API_KEY = _get_api_key()
MODEL = os.getenv("GEMINI_MODEL") or os.getenv("VITE_GEMINI_MODEL") or "gemini-3.8-flash"
# Tried in order when the main model is overloaded (503/429) or unavailable (404).
BACKUP_MODELS = [m for m in ("gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite") if m != MODEL]
st.session_state.setdefault("last_model", MODEL)

# --------------------------------------------------------------------------------------
# Content (ported from src/App.tsx)
# --------------------------------------------------------------------------------------

PHASES = [
    {
        "title": "Planning",
        "subtitle": "Define the project",
        "steps": [
            "1a · Project definition",
            "1b · Secondary research",
            "2 · User recruitment",
            "3 · Ethics & deontology",
        ],
    },
    {
        "title": "Exploration",
        "subtitle": "Collect user needs",
        "steps": [
            "4 · Interviews",
            "5 · Focus groups",
            "6 · Observation",
            "7 · Exploratory survey",
            "8 · Cultural probes",
        ],
    },
    {
        "title": "Ideation",
        "subtitle": "Synthesize & create ideas",
        "steps": [
            "9 · Brainstorming",
            "10 · Ideation cards",
            "11 · Design studio",
            "12 · Experience maps",
            "13 · Personas",
            "14 · Generative techniques",
        ],
    },
]

PAGES = [
    {
        "eyebrow": "Your project · Planning",
        "title": "Your project notebook",
        "description": "Write the project as you see it. The coach reads alongside you and suggests what to add, reconsider, or clarify using the book’s methodology.",
        "notebook_title": "Describe your project freely",
        "notebook_help": "Your words, your structure. There are no required sub-steps.",
        "coach_basis": "Planning methods 1a–3",
        "why": "At this stage, the coach looks for a clear problem, stakeholders, assumptions, constraints, and signs of success before research begins.",
    },
    {
        "eyebrow": "Your project · Exploration",
        "title": "Capture what you learn",
        "description": "Write down observations, interview notes, quotes, contradictions, and emerging patterns. Keep the evidence in your own words—the coach helps you notice what may be missing.",
        "notebook_title": "Your exploration notes",
        "notebook_help": "Record evidence before interpreting it. Quotes and concrete behaviors are valuable.",
        "coach_basis": "Exploration methods 4–8",
        "why": "The book recommends triangulating what people say, do, and create. The coach distinguishes evidence from assumptions and highlights gaps in the sample or context.",
    },
    {
        "eyebrow": "Your project · Ideation",
        "title": "Turn insights into possibilities",
        "description": "Develop opportunities and ideas from your research without judging them too early. The coach protects divergence, connects ideas to evidence, and identifies promising directions.",
        "notebook_title": "Brainstorming: your idea space",
        "notebook_help": "Generate multiple ideas before filtering them. Keep the user evidence visible and build on what emerged from exploration.",
        "coach_basis": "Ideation method 9 · Brainstorming",
        "why": "The book treats brainstorming as a divergence activity: generate lots of options, defer judgment, combine ideas, and keep the problem framing anchored in user evidence.",
    },
]

DEFAULT_SUGGESTIONS = [
    [
        {
            "id": 1,
            "type": "add",
            "importance": "high",
            "label": "Essential",
            "text": "Add measurable success criteria. Method 1a requires the team to agree on what will have improved when the mission is complete.",
            "action": "Add success criteria",
            "applyText": "Success criteria: users can complete their intended task with less friction, and the team can measure whether the solution actually improves the experience.",
        },
        {
            "id": 2,
            "type": "consider",
            "importance": "medium",
            "label": "Important",
            "text": "Map the stakeholders who influence the project and identify which groups shape the problem, the decision, or the adoption of the solution.",
            "action": "Add comment",
            "applyText": "",
        },
        {
            "id": 3,
            "type": "remove",
            "importance": "low",
            "label": "Worth refining",
            "text": "The description jumps directly to a solution. Method 1a asks you to align on the problem and objectives before committing to a format.",
            "action": "Reframe as hypothesis",
            "applyText": "Project hypothesis: People experience a meaningful friction when trying to complete this task, and the right solution format still needs to be validated through research.",
        },
    ],
    [
        {
            "id": 11,
            "type": "add",
            "importance": "high",
            "label": "Essential",
            "text": "The notes contain useful quotes, but not the context in which each behavior occurred. Method 6 recommends capturing place, time, activity, and surrounding conditions.",
            "action": "Add context prompt",
            "applyText": "Context to capture for each observation: location, time, activity, who was present, what happened immediately before, and the participant’s workaround.",
        },
        {
            "id": 12,
            "type": "consider",
            "importance": "medium",
            "label": "Important",
            "text": "Different user groups may reveal distinct patterns. Check whether your evidence is consistent across several participants before treating them as segments.",
            "action": "Add research note",
            "applyText": "",
        },
        {
            "id": 13,
            "type": "remove",
            "importance": "low",
            "label": "Watch the bias",
            "text": "“Feels suitable” is an interpretation. Preserve the observable signals—where students looked, how long they searched, and why they rejected a space.",
            "action": "Add evidence rule",
            "applyText": "Evidence rule: separate what was directly observed or quoted from the team’s interpretation.",
        },
    ],
    [
        {
            "id": 21,
            "type": "add",
            "importance": "high",
            "label": "Starred idea",
            "text": "Your strongest direction may be a trusted, context-aware concept: people need to know not just if something is available, but whether it fits their timing, task, and situation.",
            "action": "Develop this direction",
            "applyText": "Promising direction — Trustworthy context: combine availability, relevance, and user intent so people can judge whether a choice makes sense for their current need.",
        },
        {
            "id": 22,
            "type": "consider",
            "importance": "medium",
            "label": "Push further",
            "text": "Brainstorming should include alternatives that do not rely on a single source of truth alone, such as preference cues, social signals, or context-based recommendations.",
            "action": "Add creative prompt",
            "applyText": "Creative prompt: generate at least two ideas that do not depend on a single data source. How else could people judge the right option for their situation?",
        },
        {
            "id": 23,
            "type": "remove",
            "importance": "low",
            "label": "Keep divergence alive",
            "text": "Avoid narrowing too soon. Method 9 encourages quantity and combination before evaluation, so add more alternative directions before selecting one.",
            "action": "Add ideation rule",
            "applyText": "Ideation rule: defer judgment, generate at least five different directions, and cluster them by shared user need before selecting a concept.",
        },
    ],
]

# --------------------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def _client(api_key: str):
    from google import genai
    from google.genai import types

    # Give up on a slow/overloaded model after 20 s so we can try the next one.
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=20_000))


def call_gemini(prompt: str, *, temperature: float, json_mode: bool = False) -> str:
    from google.genai import types

    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )
    # Start with the model that last worked in this session, then the main and backup models.
    candidates = list(dict.fromkeys([st.session_state.last_model, MODEL, *BACKUP_MODELS]))
    last_error: Exception | None = None
    for model in candidates:
        try:
            response = _client(API_KEY).models.generate_content(model=model, contents=prompt, config=config)
            st.session_state.last_model = model
            return response.text or ""
        except Exception as error:  # noqa: BLE001
            # Bad request / bad key won't be fixed by switching models.
            if getattr(error, "code", None) in (400, 401, 403):
                raise
            last_error = error
    raise last_error  # type: ignore[misc]


def _short_error(error: Exception) -> str:
    message = str(error).replace("\n", " ")
    return message[:220] + ("…" if len(message) > 220 else "")


def fallback_prompts(project_text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", project_text).strip()
    if not normalized:
        return []
    ctx = f"{normalized[:180].strip()}…" if len(normalized) > 180 else normalized
    return [
        f'How might we reduce friction in the experience described by "{ctx}"?',
        f'What if we helped users feel more confident before making a decision in "{ctx}"?',
        f'How might we support different user needs and situations behind "{ctx}" without adding complexity?',
        f'What if the solution made the value visible earlier for users of "{ctx}"?',
        f'How might we turn the main pain point in "{ctx}" into a more rewarding experience?',
        f'What if the product adapted to user context, time, and preferences in "{ctx}"?',
    ]


def generate_brainstorm_prompts(project_text: str) -> tuple[list[str], str, str]:
    """Returns (prompts, status_kind, status_message). status_kind: ai | fallback."""
    trimmed = project_text.strip()
    if not trimmed:
        return [], "ai", ""
    if not API_KEY:
        return fallback_prompts(trimmed), "fallback", "No API key found — using local prompts."
    prompt = (
        "You are a UX ideation coach. Based on this project context, generate exactly 6 short, "
        "practical brainstorming prompts for a user-centered design project. Use the project's "
        "context. Return only the prompts, one per line, no numbering, no explanations, no markdown."
        f"\n\nProject context:\n{trimmed}"
    )
    try:
        content = call_gemini(prompt, temperature=0.9)
        prompts = [re.sub(r"^[-*•\d\s.]+", "", line).strip() for line in content.splitlines()]
        prompts = [p for p in prompts if len(p) > 12][:6]
        if prompts:
            return prompts, "ai", f"Generated by {st.session_state.last_model}"
        return fallback_prompts(trimmed), "fallback", "Gemini returned no prompts — using local prompts."
    except Exception as error:  # noqa: BLE001
        return fallback_prompts(trimmed), "fallback", f"Gemini error — using local prompts. {_short_error(error)}"


def generate_coach_suggestions(phase: int, project_text: str) -> list[dict]:
    page, info = PAGES[phase], PHASES[phase]
    prompt = f"""You are an AI coach helping beginner UX designers apply a book-based UX methodology.
Current phase: {info["title"]} ({info["subtitle"]}).
Methods available in this phase: {", ".join(info["steps"])}.
What the coach looks for at this stage: {page["why"]}

Read the designer's notebook below and return exactly 3 suggestions, ranked most important first,
as a JSON array. Each item must be an object with these keys:
- "type": "add" (something missing to add), "remove" (something to reframe, cut, or a bias to fix), or "consider" (an open question for the team to reflect on)
- "importance": "high", "medium" or "low" (first item high, then medium, then low)
- "label": 1-3 word badge, e.g. "Essential", "Important", "Watch the bias"
- "text": the suggestion, max 45 words, specific to the notebook content, citing the relevant method number
- "action": a 2-4 word button label, e.g. "Add success criteria"
- "applyText": for "add"/"remove", one or two sentences the designer could append to their notebook; for "consider", an empty string
Write in the same language as the notebook. Do not invent research findings.

Notebook:
{project_text.strip()}"""
    raw = call_gemini(prompt, temperature=0.6, json_mode=True)
    data = json.loads(raw)
    if isinstance(data, dict):
        data = data.get("suggestions") or next((v for v in data.values() if isinstance(v, list)), [])
    if not isinstance(data, list):
        raise ValueError("Unexpected response format from Gemini.")

    suggestions = []
    for item in data[:3]:
        if not isinstance(item, dict) or not str(item.get("text", "")).strip():
            continue
        s_type = item.get("type") if item.get("type") in ("add", "remove", "consider") else "consider"
        importance = item.get("importance") if item.get("importance") in ("high", "medium", "low") else "medium"
        st.session_state.next_id += 1
        suggestions.append(
            {
                "id": st.session_state.next_id,
                "type": s_type,
                "importance": importance,
                "label": str(item.get("label") or "Suggestion").strip()[:40],
                "text": str(item["text"]).strip(),
                "action": str(item.get("action") or ("Add comment" if s_type == "consider" else "Apply")).strip()[:40],
                "applyText": "" if s_type == "consider" else str(item.get("applyText") or "").strip(),
            }
        )
    if not suggestions:
        raise ValueError("Gemini returned no usable suggestions.")
    return suggestions


# --------------------------------------------------------------------------------------
# State & callbacks
# --------------------------------------------------------------------------------------


def init_state() -> None:
    ss = st.session_state
    ss.setdefault("phase", 0)
    ss.setdefault("notebooks", ["", "", ""])
    ss.setdefault("suggestions", [list(s) for s in DEFAULT_SUGGESTIONS])
    ss.setdefault("accepted", [set(), set(), set()])
    ss.setdefault("notes", [{}, {}, {}])
    ss.setdefault("ai_prompts", [])
    ss.setdefault("prompt_status", ("", ""))
    ss.setdefault("coach_status", [("", ""), ("", ""), ("", "")])
    ss.setdefault("next_id", 1000)


def change_phase(index: int) -> None:
    st.session_state.phase = index


def sync_notebook(phase: int) -> None:
    st.session_state.notebooks[phase] = st.session_state[f"w_nb_{phase}"]


def append_to_notebook(phase: int, block: str) -> None:
    current = st.session_state.notebooks[phase]
    st.session_state.notebooks[phase] = f"{current}\n\n{block}" if current.strip() else block


def accept_suggestion(phase: int, suggestion: dict) -> None:
    if suggestion["applyText"]:
        append_to_notebook(phase, suggestion["applyText"])
    st.session_state.accepted[phase].add(suggestion["id"])


def dismiss_suggestion(phase: int, sid: int) -> None:
    st.session_state.suggestions[phase] = [s for s in st.session_state.suggestions[phase] if s["id"] != sid]


def insert_prompt(prompt: str) -> None:
    if prompt not in st.session_state.notebooks[2]:
        append_to_notebook(2, f"Brainstorming prompt: {prompt}")


def overall_progress(phase: int) -> int:
    length = len(st.session_state.notebooks[phase])
    phase_progress = min(34, max(8, round(length / 22)))
    return min(100, phase * 33 + phase_progress)


def notes_markdown() -> str:
    parts = ["# UXmethod — project notes\n"]
    for i, phase in enumerate(PHASES):
        parts.append(f"## {chr(65 + i)}. {phase['title']}\n")
        parts.append((st.session_state.notebooks[i].strip() or "_Nothing written yet._") + "\n")
        notes = st.session_state.notes[i]
        if notes:
            parts.append("**Team notes**\n")
            parts.extend(f"- {n}" for n in notes.values())
            parts.append("")
    return "\n".join(parts)


# --------------------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------------------

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');

.stApp, .stApp *:not([data-testid="stIconMaterial"]) { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f7f7f4; color: #252724; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; max-width: 1500px; }
::selection { background: #dce9e2; color: #26332d; }

/* Sidebar */
[data-testid="stSidebar"] { background: #f1f1ed; border-right: 1px solid #deded8; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] {
  justify-content: flex-start; text-align: left; width: 100%;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  background: #fff; color: #252724; border: 1px solid #e3e3dd; box-shadow: 0 1px 2px rgba(0,0,0,.04);
}

/* Buttons */
[data-testid="stBaseButton-primary"] { background: #242724; border-color: #242724; color: #fff; }
[data-testid="stBaseButton-primary"]:hover { background: #000; border-color: #000; color: #fff; }
[data-testid="stBaseButton-secondary"] { border-color: #d9dad4; background: #fcfcfa; color: #3b3e39; }
[data-testid="stBaseButton-secondary"]:hover { border-color: #7fa18f; color: #2d5a48; }
[data-testid="stBaseButton-tertiary"] { color: #47715f; font-weight: 600; }

/* Header */
.ux-header { display:flex; align-items:center; gap:12px; padding: 4px 0 18px; border-bottom: 1px solid #deded8; margin-bottom: 26px; }
.ux-header img { height: 36px; width: 58px; object-fit: contain; }
.ux-header .brand { font-weight: 600; letter-spacing: -0.03em; font-size: 17px; }
.ux-header .sep { width:1px; height:20px; background:#d8d8d1; }
.ux-header .proj { font-size: 14px; font-weight: 500; color: #4b4d48; }
.ux-header .spacer { flex: 1; }
.pill { font-size: 12px; font-weight: 600; padding: 5px 11px; border-radius: 999px; }
.pill.ok { background: #dcefe5; color: #35745d; }
.pill.off { background: #f8e8ba; color: #936516; }

/* Typography */
.eyebrow { display:flex; align-items:center; gap:8px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .14em; color: #4d846f; margin-bottom: 10px; }
.eyebrow::before { content:""; width: 20px; height: 1px; background: #4d846f; }
.editorial-title { font-family: 'DM Serif Display', serif !important; font-size: clamp(2rem, 4vw, 2.75rem); line-height: 1.08; letter-spacing: -0.025em; margin: 0; color: #252724; }
.lede { margin-top: 8px; max-width: 36rem; font-size: 15px; line-height: 1.6; color: #6c6f69; margin-bottom: 28px; }
.card-title { font-size: 14px; font-weight: 600; margin: 0; }
.card-help { font-size: 12px; color: #7b7e77; margin: 2px 0 14px; }
.micro { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .12em; color: #858880; }
.muted { font-size: 12px; line-height: 1.6; color: #72756e; }

/* Cards */
[class*="st-key-card"] {
  background: #fff; border: 1px solid #deded8; border-radius: 12px;
  padding: 1.35rem 1.5rem; box-shadow: 0 1px 2px rgb(31 36 31 / 3%);
}
.st-key-card-explore { background: #f3faf7; }
.st-key-card-ideate, .st-key-card-prompts { background: #fffaf0; }
.st-key-card-why { background: rgba(255,255,255,.65); }
[class*="st-key-card"] textarea { background: #fcfcfa; font-size: 15px; line-height: 1.75; color: #343632; }

/* Chips */
.chips { display:flex; flex-wrap:wrap; gap:8px; margin: 12px 0; }
.chip { border: 1px solid #deded7; background: #fff; border-radius: 6px; padding: 6px 10px; font-size: 11px; font-weight: 500; color: #5c605a; }
.phase-chips { display:grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }
.phase-chips div { border-radius: 6px; padding: 8px; text-align:center; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; }

/* Coach panel */
.coach-head { display:flex; gap: 12px; align-items:flex-start; margin-bottom: 14px; }
.coach-icon { width: 40px; height: 40px; border-radius: 12px; background: #dfeae4; color: #43715e; display:flex; align-items:center; justify-content:center; font-size: 18px; flex-shrink: 0; }
[class*="st-key-sug-"] { border: 1px solid #deded7; border-left-width: 3px; border-radius: 8px; padding: .9rem 1rem .6rem; }
[class*="st-key-sug-add"] { border-left-color: #4f9b7d; background: #f2f8f4; }
[class*="st-key-sug-remove"] { border-left-color: #d16b61; background: #fff5f3; }
[class*="st-key-sug-consider"] { border-left-color: #d39a39; background: #fff9ec; }
[class*="st-key-sug-"][class*="-high"] { box-shadow: 0 0 0 1px rgba(213,177,99,.5); }
.rank { font-size: 10px; font-weight: 700; color: #8c8f88; margin-right: 6px; }
.badge { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .09em; padding: 4px 8px; border-radius: 6px; }
.badge-add { background: #dcefe5; color: #35745d; }
.badge-remove { background: #f9dfdc; color: #a94c43; }
.badge-consider { background: #f8e8ba; color: #936516; }
.sug-text { font-size: 13px; line-height: 1.55; color: #4f524d; margin: 8px 0 2px; }
.team-note { margin-top: 6px; border-radius: 6px; background: rgba(255,255,255,.7); padding: 8px 10px; font-size: 12px; line-height: 1.6; color: #686450; }
.applied { font-size: 12px; font-weight: 600; color: #4d846f; padding: 6px 0; }
.empty { border: 1px dashed #d5d6d0; border-radius: 12px; padding: 22px; text-align: center; font-size: 13px; color: #858781; }
.status { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: #7a6b45; margin: 4px 0 10px; }
.status.err { text-transform: none; letter-spacing: 0; font-size: 12px; color: #a94c43; }

/* Prompt bank buttons */
.st-key-card-prompts [data-testid="stBaseButton-secondary"] {
  text-align: left; justify-content: flex-start; min-height: 74px; width: 100%;
  border-color: #e7d8a2; background: rgba(255,255,255,.8); font-size: 12px; line-height: 1.5;
}
.st-key-card-prompts [data-testid="stBaseButton-secondary"]:hover { border-color: #d5b96d; background: #fffdf5; color: #4d4d4a; }
.prompt-empty { border: 1px dashed #d8c57a; border-radius: 12px; background: #fffdf7; padding: 16px; font-size: 14px; line-height: 1.6; color: #66582d; }
</style>
"""


def img_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode() if path.exists() else ""


# --------------------------------------------------------------------------------------
# Dialogs
# --------------------------------------------------------------------------------------


@st.dialog("Add a consideration")
def comment_dialog(phase: int, sid: int) -> None:
    st.markdown(
        '<p class="muted" style="font-size:14px">Keep this thought visible as your project develops. '
        "You can revisit or resolve it when you have stronger evidence.</p>",
        unsafe_allow_html=True,
    )
    note = st.text_area(
        "Note for the team",
        key=f"dlg_note_{sid}",
        placeholder="Write a note for your team…",
        height=120,
    )
    left, right = st.columns(2)
    if left.button("Cancel", width="stretch"):
        st.rerun()
    if right.button("💬 Add comment", type="primary", width="stretch"):
        if not note.strip():
            st.warning("Write a note first.")
            return
        st.session_state.notes[phase][sid] = note.strip()
        st.session_state.accepted[phase].add(sid)
        st.rerun()


@st.dialog("UX design methodology", width="large")
def library_dialog() -> None:
    st.markdown(
        '<div class="eyebrow">Book-based framework</div>'
        '<p class="muted" style="font-size:14px">The book defines five phases. This tool intentionally '
        "supports only the first three—the space where a designer frames, investigates, and develops ideas.</p>",
        unsafe_allow_html=True,
    )
    if SCOPE_IMG.exists():
        st.image(str(SCOPE_IMG), width="stretch")
    cols = st.columns(3)
    for pi, (col, phase) in enumerate(zip(cols, PHASES)):
        with col:
            st.markdown(
                f'<div class="micro">Phase {chr(65 + pi)}</div><p class="card-title">{phase["title"]}</p>',
                unsafe_allow_html=True,
            )
            for mi, method in enumerate(phase["steps"]):
                kind = "primary" if pi == st.session_state.phase else "secondary"
                if st.button(method, key=f"lib-{pi}-{mi}", type=kind, width="stretch"):
                    change_phase(pi)
                    st.rerun()
    st.markdown(
        '<p class="muted" style="margin-top:14px">🕒 In scope: framing the project, exploring user needs, '
        "synthesizing evidence, and brainstorming ideas. Out of scope: formalizing solutions and evaluating "
        "them. <b>3 phases · 15 book methods</b></p>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------------------


def render_header() -> None:
    logo = img_b64(LOGO)
    pill = (
        f'<span class="pill ok">● Gemini connected · {html.escape(MODEL)}</span>'
        if API_KEY
        else '<span class="pill off">● No API key · local fallback</span>'
    )
    st.markdown(
        f"""<div class="ux-header">
        {f'<img src="data:image/png;base64,{logo}" alt="UXmethod">' if logo else ''}
        <span class="brand">UXmethod</span><span class="sep"></span>
        <span class="proj">Your project</span><span class="spacer"></span>{pill}
        </div>""",
        unsafe_allow_html=True,
    )


def render_sidebar(phase: int) -> bool:
    open_library = False
    with st.sidebar:
        progress = overall_progress(phase)
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:12px;font-weight:500">'
            f"<span>Your progress</span><span>{progress}%</span></div>",
            unsafe_allow_html=True,
        )
        st.progress(progress / 100)
        st.write("")
        for i, info in enumerate(PHASES):
            done = "✓" if i <= phase else "○"
            st.button(
                f"**{i + 1} · {info['title']}**  \n{info['subtitle']}  {done}",
                key=f"nav-{i}",
                type="primary" if i == phase else "tertiary",
                on_click=change_phase,
                args=(i,),
                width="stretch",
            )
        st.divider()
        if st.button("📖 Book methods", type="tertiary", key="nav-library"):
            open_library = True
        st.download_button(
            "⬇ Download notes (.md)",
            data=notes_markdown(),
            file_name="uxmethod-notes.md",
            mime="text/markdown",
            width="stretch",
        )
        st.caption("Notes are kept for this browser session only — download them to keep a copy.")
    return open_library


def render_phase_card(phase: int) -> bool:
    open_library = False
    if phase == 0:
        with st.container(key="card-scope"):
            head, link = st.columns([4, 1.3])
            head.markdown(
                '<p class="card-title" style="color:#315f4d">✨ The scope of your AI brainstorming coach</p>'
                '<p class="card-help">It supports the first three phases only: planning, exploration, and ideation.</p>',
                unsafe_allow_html=True,
            )
            if link.button("Understand the scope", type="tertiary", key="scope-link"):
                open_library = True
            if SCOPE_IMG.exists():
                st.image(str(SCOPE_IMG), width="stretch")
            st.markdown(
                '<div class="phase-chips">'
                '<div style="background:#dfeaf0;color:#365f78">A. Planning</div>'
                '<div style="background:#dcefe8;color:#397160">B. Exploration</div>'
                '<div style="background:#f4edc8;color:#75682c">C. Ideation</div></div>',
                unsafe_allow_html=True,
            )
    else:
        info = PHASES[phase]
        heading = (
            "Listen, observe, and gather evidence"
            if phase == 1
            else "Diverge, connect, and develop possibilities"
        )
        footer = (
            "Use several methods when possible: interviews reveal what people say, observation shows what they do, and cultural probes reveal what they create."
            if phase == 1
            else "Ideas should build on exploration evidence. Produce broadly before grouping, developing, and eventually selecting directions."
        )
        chips = "".join(f'<span class="chip">{m}</span>' for m in info["steps"])
        with st.container(key="card-explore" if phase == 1 else "card-ideate"):
            st.markdown(
                f'<div class="micro">Methods available in this phase · {len(info["steps"])} methods</div>'
                f'<p class="card-title" style="font-size:16px;margin-top:4px">{heading}</p>'
                f'<div class="chips">{chips}</div>'
                f'<p class="muted" style="border-top:1px solid #deded8;padding-top:10px;margin:0">{footer}</p>',
                unsafe_allow_html=True,
            )
    return open_library


def render_notebook(phase: int) -> None:
    page = PAGES[phase]
    widget_key = f"w_nb_{phase}"
    st.session_state[widget_key] = st.session_state.notebooks[phase]
    with st.container(key="card-notebook"):
        st.markdown(
            f'<p class="card-title">💡 {page["notebook_title"]}</p><p class="card-help">{page["notebook_help"]}</p>',
            unsafe_allow_html=True,
        )
        st.text_area(
            page["notebook_title"],
            key=widget_key,
            height=360,
            placeholder="Write your own project idea, problem statement, user need, or opportunity here...",
            label_visibility="collapsed",
            on_change=sync_notebook,
            args=(phase,),
        )
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:12px">'
            f'<span style="color:#969892">{len(st.session_state.notebooks[phase])} characters</span>'
            f'<span style="color:#4d846f;font-weight:500">✨ AI coach is reading</span></div>',
            unsafe_allow_html=True,
        )


def render_prompt_bank() -> None:
    with st.container(key="card-prompts"):
        head, action = st.columns([3, 1.4])
        head.markdown(
            '<p class="card-title">💡 Brainstorming prompt bank</p>'
            '<p class="card-help" style="color:#766a4c">Use these prompts to stretch your ideation before selecting a direction.</p>',
            unsafe_allow_html=True,
        )
        if action.button("Generate for this project", key="gen-prompts", width="stretch"):
            with st.spinner("Generating custom prompts…"):
                prompts, kind, message = generate_brainstorm_prompts(st.session_state.notebooks[2])
            st.session_state.ai_prompts = prompts
            st.session_state.prompt_status = (kind, message)

        kind, message = st.session_state.prompt_status
        if message:
            css = "status err" if kind == "fallback" and "error" in message.lower() else "status"
            label = "Google AI Studio connected" if kind == "ai" else "Prototype fallback mode"
            st.markdown(f'<div class="{css}">{label} · {html.escape(message)}</div>', unsafe_allow_html=True)

        prompts = st.session_state.ai_prompts
        if not prompts:
            st.markdown(
                '<div class="prompt-empty">Start by writing your own project context above, then click '
                "<b>Generate for this project</b>. The prompt bank will generate ideas tailored to your brief.</div>",
                unsafe_allow_html=True,
            )
            return
        cols = st.columns(2)
        for i, prompt in enumerate(prompts):
            cols[i % 2].button(
                prompt,
                key=f"prompt-{i}-{hash(prompt)}",
                on_click=insert_prompt,
                args=(prompt,),
                width="stretch",
                help="Add this prompt to your notebook",
            )


def render_coach(phase: int) -> bool:
    page = PAGES[phase]
    open_library = False
    st.markdown(
        f'<div class="coach-head"><div class="coach-icon">✨</div><div>'
        f'<p class="card-title" style="font-size:16px">AI coach</p>'
        f'<p class="muted" style="margin:0">{page["coach_basis"]}</p></div></div>',
        unsafe_allow_html=True,
    )

    has_text = bool(st.session_state.notebooks[phase].strip())
    if st.button(
        "✨ Review with AI coach",
        key=f"review-{phase}",
        type="primary",
        width="stretch",
        disabled=not API_KEY or not has_text,
        help=None if API_KEY else "Add your Gemini API key to .env to enable AI reviews.",
    ):
        with st.spinner("The coach is reading your notebook…"):
            try:
                st.session_state.suggestions[phase] = generate_coach_suggestions(
                    phase, st.session_state.notebooks[phase]
                )
                st.session_state.accepted[phase] = set()
                st.session_state.coach_status[phase] = ("ai", f"Suggestions generated by {st.session_state.last_model} from your notebook.")
            except Exception as error:  # noqa: BLE001
                st.session_state.coach_status[phase] = ("err", f"Gemini error: {_short_error(error)}")

    kind, message = st.session_state.coach_status[phase]
    if message:
        st.markdown(
            f'<div class="status {"err" if kind == "err" else ""}">{html.escape(message)}</div>',
            unsafe_allow_html=True,
        )
    elif not has_text:
        st.caption("Write in your notebook, then ask the coach for a review. Example suggestions are shown below.")

    st.markdown(
        '<div style="display:flex;justify-content:space-between;margin:14px 0 8px">'
        '<span class="micro" style="color:#6e716b">Ranked suggestions</span>'
        '<span style="font-size:11px;color:#989a94">Most important first</span></div>',
        unsafe_allow_html=True,
    )

    suggestions = st.session_state.suggestions[phase]
    accepted = st.session_state.accepted[phase]
    notes = st.session_state.notes[phase]
    for rank, s in enumerate(suggestions, 1):
        with st.container(key=f"sug-{s['type']}-{s['id']}-{s['importance']}"):
            top, close = st.columns([6, 1])
            star = "★ " if s["importance"] == "high" else ""
            top.markdown(
                f'<span class="rank">#{rank}</span><span class="badge badge-{s["type"]}">'
                f'{star}{html.escape(s["label"])}</span>',
                unsafe_allow_html=True,
            )
            close.button(
                "✕",
                key=f"dismiss-{s['id']}",
                type="tertiary",
                on_click=dismiss_suggestion,
                args=(phase, s["id"]),
                help="Dismiss suggestion",
            )
            st.markdown(f'<p class="sug-text">{html.escape(s["text"])}</p>', unsafe_allow_html=True)
            if s["id"] in notes:
                st.markdown(
                    f'<div class="team-note"><b>Team note:</b> {html.escape(notes[s["id"]])}</div>',
                    unsafe_allow_html=True,
                )
            if s["id"] in accepted:
                st.markdown('<div class="applied">✓ Applied</div>', unsafe_allow_html=True)
            elif s["type"] == "consider":
                if st.button(f"＋ {s['action']}", key=f"act-{s['id']}", type="tertiary"):
                    comment_dialog(phase, s["id"])
            else:
                st.button(
                    f"＋ {s['action']}",
                    key=f"act-{s['id']}",
                    type="tertiary",
                    on_click=accept_suggestion,
                    args=(phase, s),
                )

    if not suggestions:
        st.markdown(
            '<div class="empty">✅<br><b style="color:#252724">All reviewed</b><br>'
            "Ask the AI coach for a new review as your notebook grows.</div>",
            unsafe_allow_html=True,
        )

    st.write("")
    with st.container(key="card-why"):
        st.markdown(
            f'<p class="card-title" style="font-size:12px">📖 Why this matters</p>'
            f'<p class="muted" style="margin:6px 0 0">{page["why"]}</p>',
            unsafe_allow_html=True,
        )
        if st.button("View supported methods", type="tertiary", key="why-methods"):
            open_library = True

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;margin-top:18px;padding-top:14px;'
        f'border-top:1px solid #deded8;font-size:12px;color:#858781">'
        f"<span>👥 Visible to your team</span><span>{PHASES[phase]['title']} active</span></div>",
        unsafe_allow_html=True,
    )
    return open_library


def main() -> None:
    st.set_page_config(
        page_title="UXmethod",
        page_icon=str(LOGO) if LOGO.exists() else "✨",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)

    phase = st.session_state.phase
    page = PAGES[phase]

    open_library = render_sidebar(phase)
    render_header()

    main_col, coach_col = st.columns([1.9, 1], gap="large")
    with main_col:
        st.markdown(
            f'<div class="eyebrow">{page["eyebrow"]}</div>'
            f'<h1 class="editorial-title">{page["title"]}</h1>'
            f'<p class="lede">{page["description"]}</p>',
            unsafe_allow_html=True,
        )
        open_library |= render_phase_card(phase)
        render_notebook(phase)
        if phase == 2:
            render_prompt_bank()
    with coach_col:
        open_library |= render_coach(phase)

    if open_library:
        library_dialog()


main()
