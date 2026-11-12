"""UXmethod — Streamlit port of the Figma Make design (src/App.tsx).

Gemini is called server-side, so the API key never reaches the browser.
Run from this folder:  streamlit run app.py
"""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import streamlit as st
from ai import API_KEY, MODEL, analyze_ideas, generate_brainstorm_prompts, generate_coach_suggestions, short_error

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
PUBLIC = ROOT / "public"
LOGO = PUBLIC / "uxmethod-logo.png"
SCOPE_IMG = PUBLIC / "methodology-scope.png"

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

METHODS = [
    {"phase": 0, "code": "1a", "title": "Project definition", "description": "Frame the request, objectives, stakeholders, constraints, and signs of success.", "notebook_title": "Define your project", "notebook_help": "Describe the problem and intended outcome before committing to a solution."},
    {"phase": 0, "code": "1b", "title": "Secondary research", "description": "Review existing knowledge, comparable services, trends, and internal resources.", "notebook_title": "Document what is already known", "notebook_help": "Capture useful sources, findings, competitors, and unanswered questions."},
    {"phase": 0, "code": "2", "title": "User recruitment", "description": "Define who should participate and how you will reach a relevant, ethical sample.", "notebook_title": "Plan your recruitment", "notebook_help": "Describe participant criteria, exclusions, channels, incentives, and target numbers."},
    {"phase": 0, "code": "3", "title": "Ethics & deontology", "description": "Protect participants through consent, privacy, transparency, and responsible data use.", "notebook_title": "Record your ethical safeguards", "notebook_help": "Note consent, sensitive topics, data handling, risks, and participant rights."},
    {"phase": 1, "code": "4", "title": "Interviews", "description": "Explore experiences, motivations, needs, and language through open conversation.", "notebook_title": "Interview notes", "notebook_help": "Keep questions, quotes, context, surprises, and follow-up points together."},
    {"phase": 1, "code": "5", "title": "Focus groups", "description": "Use group discussion to reveal shared views, disagreements, and social dynamics.", "notebook_title": "Focus group notes", "notebook_help": "Capture themes, contrasting opinions, group effects, and notable participant quotes."},
    {"phase": 1, "code": "6", "title": "Observation", "description": "Study what people actually do in context, including workarounds and environmental cues.", "notebook_title": "Observation log", "notebook_help": "Record behavior, place, time, triggers, obstacles, and your interpretation separately."},
    {"phase": 1, "code": "7", "title": "Exploratory survey", "description": "Collect broader self-reported patterns to complement qualitative exploration.", "notebook_title": "Survey plan and findings", "notebook_help": "Draft objectives and questions, then record response patterns and limitations."},
    {"phase": 1, "code": "8", "title": "Cultural probes", "description": "Invite participants to document and express parts of their everyday experience.", "notebook_title": "Cultural probe plan", "notebook_help": "Describe activities, materials, participant instructions, returns, and inspirations."},
    {"phase": 2, "code": "9", "title": "Brainstorming", "description": "Generate many varied ideas, defer judgment, and build on the thinking of others.", "notebook_title": "Brainstorming: your idea space", "notebook_help": "Generate broadly before filtering. Keep user evidence visible as you work."},
    {"phase": 2, "code": "10", "title": "Ideation cards", "description": "Use structured prompts and design principles to provoke new solution directions.", "notebook_title": "Ideas from the cards", "notebook_help": "Record each prompt, the idea it triggered, and its link to user evidence."},
    {"phase": 2, "code": "11", "title": "Design studio", "description": "Sketch, share, critique, and combine ideas collaboratively around a shared brief.", "notebook_title": "Design studio workspace", "notebook_help": "Capture the brief, individual concepts, critique notes, and combined directions."},
    {"phase": 2, "code": "12", "title": "Experience maps", "description": "Synthesize the user journey to reveal pain points, emotions, and design opportunities.", "notebook_title": "Map the experience", "notebook_help": "List stages, actions, thoughts, emotions, evidence, pain points, and opportunities."},
    {"phase": 2, "code": "13", "title": "Personas", "description": "Create evidence-based user profiles that keep important behavioral patterns visible.", "notebook_title": "Persona evidence", "notebook_help": "Describe goals, behaviors, contexts, needs, and the research supporting each pattern."},
    {"phase": 2, "code": "14", "title": "Generative techniques", "description": "Help users express tacit needs and imagine futures through creative activities.", "notebook_title": "Generative session notes", "notebook_help": "Plan the activity and capture artifacts, stories, interpretations, and emerging ideas."},
]

PHASE_DESCRIPTIONS = [
    "Frame a clear, responsible brief before you start making. Define the opportunity, gather what is already known, recruit the right people, and protect participants.",
    "Learn from people and their context. Use conversations, observation, surveys, and creative probes to uncover needs, behaviors, tensions, and opportunities.",
    "Turn evidence into possibilities. Generate broadly, connect insights, sketch directions, and keep enough variety before choosing what to develop.",
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
# State & callbacks
# --------------------------------------------------------------------------------------


def init_state() -> None:
    ss = st.session_state
    ss.setdefault("page", -1)
    if len(ss.get("notebooks", [])) != len(METHODS):
        legacy = ss.get("notebooks", ["", "", ""])
        ss.notebooks = [
            legacy[method["phase"]] if method["phase"] < len(legacy) and i == next(
                j for j, candidate in enumerate(METHODS) if candidate["phase"] == method["phase"]
            ) else ""
            for i, method in enumerate(METHODS)
        ]
    ss.setdefault("suggestions", [list(s) for s in DEFAULT_SUGGESTIONS])
    ss.setdefault("accepted", [set(), set(), set()])
    if len(ss.get("notes", [])) != len(METHODS):
        ss.notes = [{} for _ in METHODS]
    ss.setdefault("ai_prompts", [])
    ss.setdefault("prompt_status", ("", ""))
    ss.setdefault("coach_status", [("", ""), ("", ""), ("", "")])
    ss.setdefault("next_id", 1000)


def change_phase(index: int) -> None:
    st.session_state.page = next(i for i, method in enumerate(METHODS) if method["phase"] == index)


def change_page(index: int) -> None:
    st.session_state.page = index


def current_phase(page: int) -> int:
    return METHODS[page]["phase"]


def sync_notebook(page: int) -> None:
    st.session_state.notebooks[page] = st.session_state[f"w_nb_{page}"]


def append_to_notebook(page: int, block: str) -> None:
    current = st.session_state.notebooks[page]
    st.session_state.notebooks[page] = f"{current}\n\n{block}" if current.strip() else block


def submit_brainstorming_idea() -> None:
    idea = st.session_state.get("w_idea_draft", "").strip()
    if not idea:
        return
    append_to_notebook(9, idea)
    st.session_state.w_idea_draft = ""


def accept_suggestion(page: int, suggestion: dict) -> None:
    phase = current_phase(page)
    if suggestion["applyText"]:
        append_to_notebook(page, suggestion["applyText"])
    st.session_state.accepted[phase].add(suggestion["id"])


def dismiss_suggestion(phase: int, sid: int) -> None:
    st.session_state.suggestions[phase] = [s for s in st.session_state.suggestions[phase] if s["id"] != sid]


def insert_prompt(prompt: str) -> None:
    if prompt not in st.session_state.notebooks[9]:
        append_to_notebook(9, f"Brainstorming prompt: {prompt}")


def full_project_context() -> str:
    return "\n\n".join(
        f'{method["code"]} · {method["title"]}\n{st.session_state.notebooks[index].strip()}'
        for index, method in enumerate(METHODS)
        if st.session_state.notebooks[index].strip()
    )


def completed_project_context() -> str:
    return "\n\n".join(
        f'{method["code"]} · {method["title"]}\n{st.session_state.notebooks[index].strip()}'
        for index, method in enumerate(METHODS)
        if index != 9 and st.session_state.notebooks[index].strip()
    )


def idea_lines() -> list[str]:
    return [
        re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
        for line in st.session_state.notebooks[9].splitlines()
        if line.strip()
    ]


def overall_progress(page: int) -> int:
    started = sum(bool(text.strip()) for text in st.session_state.notebooks)
    return round(started / len(METHODS) * 100)


def notes_markdown() -> str:
    parts = ["# UXmethod — project notes\n"]
    for phase_index, phase in enumerate(PHASES):
        parts.append(f"## {chr(65 + phase_index)}. {phase['title']}\n")
        for i, method in enumerate(METHODS):
            if method["phase"] != phase_index:
                continue
            parts.append(f'### {method["code"]} · {method["title"]}\n')
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
.phase-number { width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border-radius:999px; background:#dce9e2; color:#3c705b; font-weight:700; margin-bottom:12px; }
.idea-map { position:relative; min-height:480px; border:1px solid #d8e2db; border-radius:12px; background:linear-gradient(to right, transparent 49.8%, #dce7df 50%, transparent 50.2%),linear-gradient(to bottom, transparent 49.8%, #dce7df 50%, transparent 50.2%),#f8fbf8; margin:12px 0 16px; }
.idea-point { position:absolute; transform:translate(-50%,-50%); width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:2px solid white; border-radius:999px; background:#4d846f; color:white; font-size:12px; font-weight:700; box-shadow:0 2px 6px rgba(0,0,0,.15); }
.map-label,.map-axis { position:absolute; color:#829189; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
.map-label { left:12px; top:10px; }.map-axis { right:12px; bottom:10px; }
.idea-row { display:flex; gap:10px; padding:9px 0; border-top:1px solid #e0e5df; font-size:12px; line-height:1.45; color:#666b64; }
.idea-row b { display:flex; width:22px; height:22px; align-items:center; justify-content:center; border-radius:999px; background:#dce9e2; color:#3d725b; flex-shrink:0; }
.idea-row strong { color:#47715f; }
</style>
"""


def img_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode() if path.exists() else ""


# --------------------------------------------------------------------------------------
# Dialogs
# --------------------------------------------------------------------------------------


@st.dialog("Add a consideration")
def comment_dialog(page: int, sid: int) -> None:
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
        phase = current_phase(page)
        st.session_state.notes[page][sid] = note.strip()
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
        else '<span class="pill off">● No API key</span>'
    )
    project_name = st.session_state.get("project_name", "").strip() or "Your project"
    st.markdown(
        f"""<div class="ux-header">
        {f'<img src="data:image/png;base64,{logo}" alt="UXmethod">' if logo else ''}
        <span class="brand">UXmethod</span><span class="sep"></span>
        <span class="proj">{html.escape(project_name)}</span><span class="spacer"></span>{pill}
        </div>""",
        unsafe_allow_html=True,
    )


def render_sidebar(page: int) -> bool:
    open_library = False
    with st.sidebar:
        progress = overall_progress(page)
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:12px;font-weight:500">'
            f"<span>Your progress</span><span>{progress}%</span></div>",
            unsafe_allow_html=True,
        )
        st.progress(progress / 100)
        st.write("")
        if st.button("⌂  Project overview", key="nav-home", type="primary" if page == -1 else "tertiary", width="stretch"):
            st.session_state.page = -1
            st.rerun()
        for phase_index, info in enumerate(PHASES):
            st.markdown(f'<div class="micro" style="margin-top:14px">{phase_index + 1}. {info["title"]}</div>', unsafe_allow_html=True)
            for method_index, method in enumerate(METHODS):
                if method["phase"] != phase_index:
                    continue
                done = "✓" if st.session_state.notebooks[method_index].strip() else "○"
                st.button(
                    f"{method['code']} · {method['title']}  {done}",
                    key=f"nav-method-{method_index}",
                    type="primary" if method_index == page else "tertiary",
                    on_click=change_page,
                    args=(method_index,),
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


def render_overview() -> None:
    st.markdown(
        '<div class="eyebrow">Start here</div><h1 class="editorial-title">Make sense of the messy middle.</h1>'
        '<p class="lede">UXmethod helps you move from an open question to grounded ideas. Capture what you know, learn from people, then make and compare possibilities without losing the thread.</p>',
        unsafe_allow_html=True,
    )
    with st.container(key="card-overview"):
        st.markdown('<p class="micro">Name your project</p>', unsafe_allow_html=True)
        st.text_input(
            "Project name",
            key="project_name",
            placeholder="e.g. A better way to find study spaces",
            label_visibility="collapsed",
        )
        st.caption("This name is saved for this browser session and appears in the header.")
    st.markdown('<div class="micro" style="margin-top:24px">Your three-part journey</div><h2 style="margin-top:4px">Choose where to begin</h2>', unsafe_allow_html=True)
    cols = st.columns(3)
    for index, (col, phase) in enumerate(zip(cols, PHASES)):
        with col:
            with st.container(key=f"overview-phase-{index}"):
                st.markdown(
                    f'<div class="phase-number">{index + 1}</div><p class="card-title">{phase["title"]}</p>'
                    f'<p class="muted">{phase["subtitle"]}</p><p class="muted" style="margin-top:12px">{PHASE_DESCRIPTIONS[index]}</p>',
                    unsafe_allow_html=True,
                )
                if st.button(f"Open {phase['title']}", key=f"overview-open-{index}", width="stretch"):
                    change_phase(index)
                    st.rerun()


def render_idea_landscape() -> None:
    ideas = idea_lines()
    with st.container(key="card-landscape"):
        st.markdown(
            f'<p class="card-title">📊 Idea landscape <span class="pill ok" style="float:right">{len(ideas)} ideas</span></p>'
            '<p class="card-help">Gemini places each idea on a visual map for quick review.</p>',
            unsafe_allow_html=True,
        )
        if not ideas:
            st.markdown('<div class="prompt-empty">Your ideas will appear here as you write them above, one per line.</div>', unsafe_allow_html=True)
            return
        analysis = analyze_ideas(ideas, full_project_context())
        points = "".join(
            f'<span class="idea-point" title="{html.escape(item["text"])}" style="left:{item["x"]}%;top:{item["y"]}%">{item["id"]}</span>'
            for item in analysis
        )
        st.markdown(
            f'<div class="idea-map"><span class="map-label">More exploratory</span>{points}<span class="map-axis">More actionable →</span></div>',
            unsafe_allow_html=True,
        )
        for item in analysis:
            st.markdown(
                f'<div class="idea-row"><b>{item["id"]}</b><span><strong>{html.escape(item["dimension"])}</strong><br>{html.escape(item["text"])}</span></div>',
                unsafe_allow_html=True,
            )


def render_notebook(page_index: int) -> None:
    page = METHODS[page_index]
    widget_key = f"w_nb_{page_index}"
    with st.container(key="card-notebook"):
        st.markdown(
            f'<p class="card-title">💡 {page["notebook_title"]}</p><p class="card-help">{page["notebook_help"]}</p>',
            unsafe_allow_html=True,
        )
        if page["code"] == "9":
            st.text_input(
                page["notebook_title"],
                key="w_idea_draft",
                placeholder="Write one short idea, then press Enter…",
                label_visibility="collapsed",
                on_change=submit_brainstorming_idea,
            )
            st.caption("Press Enter after each idea. It will be saved below and the input will clear.")
        else:
            st.session_state[widget_key] = st.session_state.notebooks[page_index]
            st.text_area(
                page["notebook_title"],
                key=widget_key,
                height=360,
                placeholder="Write your notes here…",
                label_visibility="collapsed",
                on_change=sync_notebook,
                args=(page_index,),
            )
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:12px">'
            f'<span style="color:#969892">{len(st.session_state.notebooks[page_index])} characters</span>'
            f'<span style="color:#4d846f;font-weight:500">✨ AI coach is reading</span></div>',
            unsafe_allow_html=True,
        )


def render_prompt_bank() -> None:
    context = completed_project_context()
    signature = context
    if context and st.session_state.get("prompt_context_signature") != signature:
        with st.spinner("Gemini is finding ways to bring this project to life…"):
            prompts, kind, message = generate_brainstorm_prompts(context)
        st.session_state.ai_prompts = prompts
        st.session_state.prompt_status = (kind, message)
        st.session_state.prompt_context_signature = signature
    with st.container(key="card-prompts"):
        head, action = st.columns([3, 1.4])
        head.markdown(
            '<p class="card-title">💡 Brainstorming prompt bank</p>'
            '<p class="card-help" style="color:#766a4c">Use these prompts to stretch your ideation before selecting a direction.</p>',
            unsafe_allow_html=True,
        )
        if action.button("Generate for this project", key="gen-prompts", width="stretch"):
            with st.spinner("Generating custom prompts…"):
                prompts, kind, message = generate_brainstorm_prompts(full_project_context())
            st.session_state.ai_prompts = prompts
            st.session_state.prompt_status = (kind, message)

        kind, message = st.session_state.prompt_status
        if message:
            css = "status err" if kind == "error" else "status"
            label = "Google AI Studio connected" if kind == "ai" else "Gemini unavailable"
            st.markdown(f'<div class="{css}">{label} · {html.escape(message)}</div>', unsafe_allow_html=True)

        prompts = st.session_state.ai_prompts
        if not prompts:
            st.markdown(
                '<div class="prompt-empty">Complete any earlier project section and Gemini will suggest '
                "ways to bring your project to life here.</div>",
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


def render_coach(phase: int, page_index: int) -> bool:
    page = PAGES[phase]
    open_library = False
    st.markdown(
        f'<div class="coach-head"><div class="coach-icon">✨</div><div>'
        f'<p class="card-title" style="font-size:16px">AI coach</p>'
        f'<p class="muted" style="margin:0">{page["coach_basis"]}</p></div></div>',
        unsafe_allow_html=True,
    )

    has_text = bool(st.session_state.notebooks[page_index].strip())
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
                suggestions = generate_coach_suggestions(
                    phase, st.session_state.notebooks[page_index], PHASES, PAGES
                )
                for suggestion in suggestions:
                    st.session_state.next_id += 1
                    suggestion["id"] = st.session_state.next_id
                st.session_state.suggestions[phase] = suggestions
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
    notes = st.session_state.notes[page_index]
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
                    comment_dialog(page_index, s["id"])
            else:
                st.button(
                    f"＋ {s['action']}",
                    key=f"act-{s['id']}",
                    type="tertiary",
                    on_click=accept_suggestion,
                    args=(page_index, s),
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

    page_index = st.session_state.page
    open_library = render_sidebar(page_index)
    render_header()

    if page_index == -1:
        render_overview()
    else:
        method = METHODS[page_index]
        phase = method["phase"]
        main_col, coach_col = st.columns([1.9, 1], gap="large")
        with main_col:
            st.markdown(
                f'<div class="eyebrow">{PHASES[phase]["title"]} · Method {method["code"]}</div>'
                f'<h1 class="editorial-title">{method["title"]}</h1>'
                f'<p class="lede">{method["description"]}</p>',
                unsafe_allow_html=True,
            )
            render_notebook(page_index)
            if method["code"] == "9":
                render_prompt_bank()
                render_idea_landscape()
        with coach_col:
            open_library |= render_coach(phase, page_index)

    if open_library:
        library_dialog()


main()
