import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  Clock3,
  HelpCircle,
  Lightbulb,
  Menu,
  MessageCircle,
  MoreHorizontal,
  Plus,
  Sparkles,
  Star,
  UserRound,
  Users,
  X,
} from "lucide-react";

type SuggestionType = "add" | "remove" | "consider";
type Suggestion = {
  id: number;
  type: SuggestionType;
  importance: "high" | "medium" | "low";
  label: string;
  text: string;
  action: string;
  applyText: string;
};

const phases = [
  {
    title: "Planning",
    subtitle: "Define the project",
    steps: [
      "1a · Project definition",
      "1b · Secondary research",
      "2 · User recruitment",
      "3 · Ethics & deontology",
    ],
  },
  {
    title: "Exploration",
    subtitle: "Collect user needs",
    steps: [
      "4 · Interviews",
      "5 · Focus groups",
      "6 · Observation",
      "7 · Exploratory survey",
      "8 · Cultural probes",
    ],
  },
  {
    title: "Ideation",
    subtitle: "Synthesize & create ideas",
    steps: [
      "9 · Brainstorming",
      "10 · Ideation cards",
      "11 · Design studio",
      "12 · Experience maps",
      "13 · Personas",
      "14 · Generative techniques",
    ],
  },
];

const pageData = [
  {
    eyebrow: "Your project · Planning",
    title: "Your project notebook",
    description:
      "Write the project as you see it. The coach reads alongside you and suggests what to add, reconsider, or clarify using the book’s methodology.",
    notebookTitle: "Describe your project freely",
    notebookHelp: "Your words, your structure. There are no required sub-steps.",
    initial: "",
    coachBasis: "Planning methods 1a–3",
    why: "At this stage, the coach looks for a clear problem, stakeholders, assumptions, constraints, and signs of success before research begins.",
  },
  {
    eyebrow: "Your project · Exploration",
    title: "Capture what you learn",
    description:
      "Write down observations, interview notes, quotes, contradictions, and emerging patterns. Keep the evidence in your own words—the coach helps you notice what may be missing.",
    notebookTitle: "Your exploration notes",
    notebookHelp:
      "Record evidence before interpreting it. Quotes and concrete behaviors are valuable.",
    initial: "",
    coachBasis: "Exploration methods 4–8",
    why: "The book recommends triangulating what people say, do, and create. The coach distinguishes evidence from assumptions and highlights gaps in the sample or context.",
  },
  {
    eyebrow: "Your project · Ideation",
    title: "Turn insights into possibilities",
    description:
      "Develop opportunities and ideas from your research without judging them too early. The coach protects divergence, connects ideas to evidence, and identifies promising directions.",
    notebookTitle: "Brainstorming: your idea space",
    notebookHelp:
      "Generate multiple ideas before filtering them. Keep the user evidence visible and build on what emerged from exploration.",
    initial: "",
    coachBasis: "Ideation method 9 · Brainstorming",
    why: "The book treats brainstorming as a divergence activity: generate lots of options, defer judgment, combine ideas, and keep the problem framing anchored in user evidence.",
  },
];

function buildContextualFallbackPrompts(projectText: string): string[] {
  const normalized = projectText.replace(/\s+/g, " ").trim();
  if (!normalized) return [];

  const context = normalized.length > 180 ? `${normalized.slice(0, 180).trim()}…` : normalized;
  const safeContext = context || "your project idea";

  return [
    `How might we reduce friction in the experience described by "${safeContext}"?`,
    `What if we helped users feel more confident before making a decision in "${safeContext}"?`,
    `How might we support different user needs and situations behind "${safeContext}" without adding complexity?`,
    `What if the solution made the value visible earlier for users of "${safeContext}"?`,
    `How might we turn the main pain point in "${safeContext}" into a more rewarding experience?`,
    `What if the product adapted to user context, time, and preferences in "${safeContext}"?`,
  ];
}

async function generateCustomBrainstormingPrompts(projectText: string): Promise<string[]> {
  const fallback = buildContextualFallbackPrompts(projectText);
  const trimmed = projectText.trim();
  if (!trimmed) return [];

  const googleApiKey = import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_GOOGLE_API_KEY;
  if (!googleApiKey) return fallback;

  const model = import.meta.env.VITE_GEMINI_MODEL || "gemini-2.0-flash";
  const baseUrl =
    import.meta.env.VITE_GEMINI_BASE_URL ||
    "https://generativelanguage.googleapis.com/v1beta/models";

  try {
    const response = await fetch(`${baseUrl}/${model}:generateContent?key=${googleApiKey}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        contents: [
          {
            role: "user",
            parts: [
              {
                text: `You are a UX ideation coach. Based on this project context, generate exactly 6 short, practical brainstorming prompts for a user-centered design project. Use the project's context. Return only the prompts, one per line, no numbering, no explanations, no markdown.\n\nProject context:\n${trimmed}`,
              },
            ],
          },
        ],
        generationConfig: {
          temperature: 0.9,
          maxOutputTokens: 260,
        },
      }),
    });

    if (!response.ok) throw new Error(`AI request failed: ${response.status}`);

    const data = await response.json();
    const content =
      data?.candidates?.[0]?.content?.parts
        ?.map((part: { text?: string }) => part.text ?? "")
        .join("\n") ?? "";

    const prompts = content
      .split(/\n+/)
      .map((line) => line.replace(/^[-*•\d\s.]+/, "").trim())
      .filter((line) => line.length > 12)
      .slice(0, 6);

    return prompts.length > 0 ? prompts : fallback;
  } catch (error) {
    console.warn(
      "Google AI Studio brainstorming generation failed, using contextual fallback.",
      error,
    );
    return fallback;
  }
}

const suggestionsByPhase: Suggestion[][] = [
  [
    {
      id: 1,
      type: "add",
      importance: "high",
      label: "Essential",
      text: "Add measurable success criteria. Method 1a requires the team to agree on what will have improved when the mission is complete.",
      action: "Add success criteria",
      applyText:
        "Success criteria: users can complete their intended task with less friction, and the team can measure whether the solution actually improves the experience.",
    },
    {
      id: 2,
      type: "consider",
      importance: "medium",
      label: "Important",
      text: "Map the stakeholders who influence the project and identify which groups shape the problem, the decision, or the adoption of the solution.",
      action: "Add comment",
      applyText: "",
    },
    {
      id: 3,
      type: "remove",
      importance: "low",
      label: "Worth refining",
      text: "The description jumps directly to a solution. Method 1a asks you to align on the problem and objectives before committing to a format.",
      action: "Reframe as hypothesis",
      applyText:
        "Project hypothesis: People experience a meaningful friction when trying to complete this task, and the right solution format still needs to be validated through research.",
    },
  ],
  [
    {
      id: 11,
      type: "add",
      importance: "high",
      label: "Essential",
      text: "The notes contain useful quotes, but not the context in which each behavior occurred. Method 6 recommends capturing place, time, activity, and surrounding conditions.",
      action: "Add context prompt",
      applyText:
        "Context to capture for each observation: location, time, activity, who was present, what happened immediately before, and the participant’s workaround.",
    },
    {
      id: 12,
      type: "consider",
      importance: "medium",
      label: "Important",
      text: "Different user groups may reveal distinct patterns. Check whether your evidence is consistent across several participants before treating them as segments.",
      action: "Add research note",
      applyText: "",
    },
    {
      id: 13,
      type: "remove",
      importance: "low",
      label: "Watch the bias",
      text: "“Feels suitable” is an interpretation. Preserve the observable signals—where students looked, how long they searched, and why they rejected a space.",
      action: "Add evidence rule",
      applyText:
        "Evidence rule: separate what was directly observed or quoted from the team’s interpretation.",
    },
  ],
  [
    {
      id: 21,
      type: "add",
      importance: "high",
      label: "Starred idea",
      text: "Your strongest direction may be a trusted, context-aware concept: people need to know not just if something is available, but whether it fits their timing, task, and situation.",
      action: "Develop this direction",
      applyText:
        "Promising direction — Trustworthy context: combine availability, relevance, and user intent so people can judge whether a choice makes sense for their current need.",
    },
    {
      id: 22,
      type: "consider",
      importance: "medium",
      label: "Push further",
      text: "Brainstorming should include alternatives that do not rely on a single source of truth alone, such as preference cues, social signals, or context-based recommendations.",
      action: "Add creative prompt",
      applyText:
        "Creative prompt: generate at least two ideas that do not depend on a single data source. How else could people judge the right option for their situation?",
    },
    {
      id: 23,
      type: "remove",
      importance: "low",
      label: "Keep divergence alive",
      text: "Avoid narrowing too soon. Method 9 encourages quantity and combination before evaluation, so add more alternative directions before selecting one.",
      action: "Add ideation rule",
      applyText:
        "Ideation rule: defer judgment, generate at least five different directions, and cluster them by shared user need before selecting a concept.",
    },
  ],
];

const typeStyles: Record<SuggestionType, { shell: string; badge: string }> = {
  add: {
    shell: "border-l-[#4f9b7d] bg-[#f2f8f4]",
    badge: "bg-[#dcefe5] text-[#35745d]",
  },
  remove: {
    shell: "border-l-[#d16b61] bg-[#fff5f3]",
    badge: "bg-[#f9dfdc] text-[#a94c43]",
  },
  consider: {
    shell: "border-l-[#d39a39] bg-[#fff9ec]",
    badge: "bg-[#f8e8ba] text-[#936516]",
  },
};

function App() {
  const [activePhase, setActivePhase] = useState(0);
  const [notebooks, setNotebooks] = useState<string[]>(() => {
    return pageData.map((page, index) => {
      const legacyPlanning = index === 0 ? localStorage.getItem("method-project-text") : null;
      return localStorage.getItem(`method-notebook-${index}`) || legacyPlanning || page.initial;
    });
  });
  const [visibleSuggestions, setVisibleSuggestions] = useState(suggestionsByPhase[0]);
  const [accepted, setAccepted] = useState<number[]>([]);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState("");
  const [commentSaved, setCommentSaved] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [coachOpen, setCoachOpen] = useState(false);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [saved, setSaved] = useState(true);
  const [aiPrompts, setAiPrompts] = useState<string[]>([]);
  const [isGeneratingPrompts, setIsGeneratingPrompts] = useState(false);
  const [aiStatus, setAiStatus] = useState<"ready" | "fallback" | "loading">("ready");

  useEffect(() => {
    if (activePhase !== 2) return;

    const timer = window.setTimeout(async () => {
      const generated = await generateCustomBrainstormingPrompts(
        notebooks[2] || pageData[2].initial,
      );
      setAiPrompts(generated);
      setAiStatus(
        import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_GOOGLE_API_KEY
          ? "ready"
          : "fallback",
      );
    }, 350);

    return () => window.clearTimeout(timer);
  }, [activePhase, notebooks]);

  useEffect(() => {
    setSaved(false);
    const timer = window.setTimeout(() => {
      notebooks.forEach((text, index) => {
        localStorage.setItem(`method-notebook-${index}`, text);
      });
      setSaved(true);
    }, 450);
    return () => window.clearTimeout(timer);
  }, [notebooks]);

  const overallProgress = useMemo(() => {
    const phaseProgress = Math.min(34, Math.max(8, Math.round(notebooks[activePhase].length / 22)));
    return Math.min(100, activePhase * 33 + phaseProgress);
  }, [activePhase, notebooks]);

  const page = pageData[activePhase];
  const projectText = notebooks[activePhase];

  function setProjectText(value: string | ((text: string) => string)) {
    setNotebooks((current) =>
      current.map((text, index) => {
        if (index !== activePhase) return text;
        return typeof value === "function" ? value(text) : value;
      }),
    );
  }

  async function generateBrainstormingPrompts() {
    if (activePhase !== 2) return;

    if (!notebooks[2].trim()) {
      setAiPrompts([]);
      setAiStatus("ready");
      setIsGeneratingPrompts(false);
      return;
    }

    setIsGeneratingPrompts(true);
    setAiStatus("loading");

    const generated = await generateCustomBrainstormingPrompts(notebooks[2]);
    setAiPrompts(generated);
    setAiStatus(
      import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_GOOGLE_API_KEY
        ? "ready"
        : "fallback",
    );
    setIsGeneratingPrompts(false);
  }

  function insertBrainstormingPrompt(prompt: string) {
    setProjectText((text) => {
      const block = `\n\nBrainstorming prompt: ${prompt}`;
      if (text.includes(prompt)) return text;
      return `${text}${block}`;
    });
  }

  function changePhase(index: number) {
    setActivePhase(index);
    setVisibleSuggestions(suggestionsByPhase[index]);
    setAccepted([]);
    setComment("");
    setCommentSaved(false);
    setShowComment(false);
    setSidebarOpen(false);
  }

  function acceptSuggestion(suggestion: Suggestion) {
    if (suggestion.type === "consider") {
      setShowComment(true);
      return;
    }
    setProjectText((text) => `${text}\n\n${suggestion.applyText}`);
    setAccepted((items) => [...items, suggestion.id]);
  }

  function dismissSuggestion(id: number) {
    setVisibleSuggestions((items) => items.filter((item) => item.id !== id));
  }

  function saveComment() {
    if (!comment.trim()) return;
    setCommentSaved(true);
    const consideration = visibleSuggestions.find((suggestion) => suggestion.type === "consider");
    if (consideration) setAccepted((items) => [...items, consideration.id]);
    window.setTimeout(() => setShowComment(false), 650);
  }

  return (
    <div className="min-h-screen bg-[#f7f7f4] text-[#252724]">
      <header className="h-[68px] border-b border-[#deded8] bg-[#fbfbf9] px-4 sm:px-6">
        <div className="mx-auto flex h-full max-w-[1600px] items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              className="icon-button lg:hidden"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open project navigation"
            >
              <Menu size={19} />
            </button>
            <img src="/uxmethod-logo.png" alt="UXmethod" className="h-9 w-[58px] object-contain" />
            <span className="font-semibold tracking-[-0.03em]">UXmethod</span>
            <span className="hidden h-5 w-px bg-[#d8d8d1] sm:block" />
            <button className="hidden items-center gap-2 text-sm font-medium text-[#4b4d48] sm:flex">
              Your project
              <ChevronDown size={15} />
            </button>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <span className="hidden items-center gap-1.5 text-xs text-[#72756e] sm:flex">
              <Check size={14} className="text-[#48846c]" />
              {saved ? "Saved locally" : "Saving…"}
            </span>
            <div className="hidden -space-x-2 md:flex">
              <div className="avatar bg-[#c7d8cf]">LM</div>
              <div className="avatar bg-[#ddcfbe]">JD</div>
              <button className="avatar bg-white text-[#676a64]">
                <Plus size={13} />
              </button>
            </div>
            <button className="rounded-lg bg-[#242724] px-4 py-2 text-sm font-medium text-white transition hover:bg-black">
              Share
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1600px]">
        {sidebarOpen && (
          <button
            className="fixed inset-0 z-30 bg-black/25 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          />
        )}
        <aside
          className={`fixed inset-y-0 left-0 z-40 w-[292px] border-r border-[#deded8] bg-[#f1f1ed] transition-transform lg:static lg:z-auto lg:min-h-[calc(100vh-68px)] lg:translate-x-0 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-[68px] items-center justify-between border-b border-[#deded8] px-5 lg:hidden">
            <span className="font-semibold">Project guide</span>
            <button className="icon-button" onClick={() => setSidebarOpen(false)}>
              <X size={18} />
            </button>
          </div>
          <div className="flex h-[calc(100%-68px)] flex-col px-4 py-6 lg:h-[calc(100vh-68px)]">
            <div className="mb-7 px-2">
              <div className="mb-2 flex items-center justify-between text-xs font-medium">
                <span>Your progress</span>
                <span>{overallProgress}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-[#dbdcd6]">
                <div
                  className="h-full rounded-full bg-[#4d846f] transition-all"
                  style={{ width: `${overallProgress}%` }}
                />
              </div>
            </div>

            <nav className="flex-1 space-y-1 overflow-y-auto">
              {phases.map((phase, index) => (
                <button
                  key={phase.title}
                  onClick={() => changePhase(index)}
                  className={`flex w-full items-start gap-3 rounded-lg px-2 py-3 text-left ${
                    index === activePhase ? "bg-white shadow-[0_1px_2px_rgba(0,0,0,.04)]" : ""
                  }`}
                >
                  <span
                    className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                      index === activePhase
                        ? "bg-[#dce9e2] text-[#3c705b]"
                        : "border border-[#cfd0ca] text-[#777a74]"
                    }`}
                  >
                    {index + 1}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold">{phase.title}</span>
                    <span className="block text-xs text-[#777a74]">{phase.subtitle}</span>
                  </span>
                  {index <= activePhase ? (
                    <CheckCircle2 size={16} className="mt-1 text-[#4d846f]" />
                  ) : (
                    <Circle size={15} className="mt-1 text-[#a3a59f]" />
                  )}
                </button>
              ))}
            </nav>

            <div className="mt-5 border-t border-[#d8d9d3] pt-4">
              <button
                onClick={() => setLibraryOpen(true)}
                className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#5c5f59] hover:bg-white/70"
              >
                <BookOpen size={17} />
                Book methods
              </button>
              <button className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#5c5f59] hover:bg-white/70">
                <HelpCircle size={17} />
                Get help
              </button>
            </div>
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <div className="grid min-h-[calc(100vh-68px)] xl:grid-cols-[minmax(0,1fr)_390px]">
            <section className="min-w-0 px-5 py-8 sm:px-9 lg:px-12 lg:py-10">
              <div className="mx-auto max-w-[760px]">
                <div className="mb-9">
                  <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-[#4d846f]">
                    <span className="h-px w-5 bg-[#4d846f]" />
                    {page.eyebrow}
                  </div>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h1 className="editorial-title">{page.title}</h1>
                      <p className="mt-2 max-w-xl text-[15px] leading-6 text-[#6c6f69]">
                        {page.description}
                      </p>
                    </div>
                    <button className="icon-button mt-1">
                      <MoreHorizontal size={19} />
                    </button>
                  </div>
                </div>

                {activePhase === 0 ? (
                  <div className="paper-card mb-6 overflow-hidden p-0">
                    <div className="flex flex-col gap-3 border-b border-[#e2e2dc] bg-[#f3f7f4] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <div className="flex items-center gap-2 text-sm font-semibold text-[#315f4d]">
                          <Sparkles size={16} />
                          The scope of your AI brainstorming coach
                        </div>
                        <p className="mt-1 text-xs leading-5 text-[#68716b]">
                          It supports the first three phases only: planning, exploration, and
                          ideation.
                        </p>
                      </div>
                      <button
                        onClick={() => setLibraryOpen(true)}
                        className="shrink-0 text-left text-xs font-semibold text-[#47715f]"
                      >
                        Understand the scope
                      </button>
                    </div>
                    <div className="bg-white p-3 sm:p-4">
                      <img
                        src="/methodology-scope.png"
                        alt="UX methodology cycle showing Planning, Exploration, Ideation, Generation, and Evaluation. This tool covers the first three phases."
                        className="h-auto w-full rounded-md"
                      />
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        {["A. Planning", "B. Exploration", "C. Ideation"].map((phase, index) => (
                          <div
                            key={phase}
                            className={`rounded-md px-2 py-2 text-center text-[10px] font-bold uppercase tracking-[0.05em] sm:text-xs ${
                              index === 0
                                ? "bg-[#dfeaf0] text-[#365f78]"
                                : index === 1
                                  ? "bg-[#dcefe8] text-[#397160]"
                                  : "bg-[#f4edc8] text-[#75682c]"
                            }`}
                          >
                            {phase}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div
                    className={`paper-card mb-6 ${
                      activePhase === 1 ? "bg-[#f3faf7]" : "bg-[#fffaf0]"
                    }`}
                  >
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#858880]">
                          Methods available in this phase
                        </div>
                        <h2 className="mt-1 text-base font-semibold">
                          {activePhase === 1
                            ? "Listen, observe, and gather evidence"
                            : "Diverge, connect, and develop possibilities"}
                        </h2>
                      </div>
                      <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-[#696c66]">
                        {phases[activePhase].steps.length} methods
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {phases[activePhase].steps.map((method) => (
                        <span
                          key={method}
                          className="rounded-md border border-[#deded7] bg-white px-2.5 py-1.5 text-[11px] font-medium text-[#5c605a]"
                        >
                          {method}
                        </span>
                      ))}
                    </div>
                    <p className="mt-4 border-t border-[#deded8] pt-3 text-xs leading-5 text-[#72756e]">
                      {activePhase === 1
                        ? "Use several methods when possible: interviews reveal what people say, observation shows what they do, and cultural probes reveal what they create."
                        : "Ideas should build on exploration evidence. Produce broadly before grouping, developing, and eventually selecting directions."}
                    </p>
                  </div>
                )}

                <div className="paper-card mb-6">
                  <div className="mb-5 flex items-center gap-3">
                    <div className="flex size-9 items-center justify-center rounded-lg bg-[#e3ebe6] text-[#42735f]">
                      <Lightbulb size={18} />
                    </div>
                    <div>
                      <h2 className="text-sm font-semibold">{page.notebookTitle}</h2>
                      <p className="text-xs text-[#7b7e77]">{page.notebookHelp}</p>
                    </div>
                  </div>
                  <textarea
                    value={projectText}
                    onChange={(event) => setProjectText(event.target.value)}
                    placeholder="Write your own project idea, problem statement, user need, or opportunity here..."
                    className="min-h-[360px] w-full resize-y rounded-lg border border-[#d9dad4] bg-[#fcfcfa] p-5 text-[15px] leading-7 text-[#343632] outline-none transition placeholder:text-[#9aa099] focus:border-[#7fa18f] focus:ring-3 focus:ring-[#dce9e2]/70"
                    aria-label="Project idea"
                  />
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-xs text-[#969892]">{projectText.length} characters</span>
                    <span className="flex items-center gap-1.5 text-xs font-medium text-[#4d846f]">
                      <Sparkles size={13} />
                      AI coach is reading
                    </span>
                  </div>
                </div>

                {activePhase === 2 && (
                  <div className="paper-card mb-6 bg-[#fffaf0]">
                    <div className="mb-4 flex items-center gap-3">
                      <div className="flex size-9 items-center justify-center rounded-lg bg-[#f4e7bd] text-[#7d5e1d]">
                        <Lightbulb size={17} />
                      </div>
                      <div className="flex-1">
                        <h2 className="text-sm font-semibold">Brainstorming prompt bank</h2>
                        <p className="text-xs text-[#766a4c]">
                          Use these prompts to stretch your ideation before selecting a direction.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={generateBrainstormingPrompts}
                        disabled={isGeneratingPrompts}
                        className="rounded-lg border border-[#d6bc72] bg-[#fffdf7] px-3 py-2 text-[11px] font-semibold text-[#6a5623] transition hover:bg-[#fffaf0] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isGeneratingPrompts ? "Generating…" : "Generate for this project"}
                      </button>
                    </div>

                    <div className="mb-3 flex items-center justify-between gap-3 text-[10px] font-medium uppercase tracking-[0.08em] text-[#7a6b45]">
                      <span>
                        {aiStatus === "ready"
                          ? "Google AI Studio connected"
                          : aiStatus === "loading"
                            ? "Generating custom prompts"
                            : "Prototype fallback mode"}
                      </span>
                      <span>
                        {import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_GOOGLE_API_KEY
                          ? "AI"
                          : "Local"}
                      </span>
                    </div>

                    {aiPrompts.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-[#d8c57a] bg-[#fffdf7] p-4 text-sm leading-6 text-[#66582d]">
                        Start by writing your own project context above. Once there is content to
                        work from, the prompt bank will generate ideas tailored to your brief.
                      </div>
                    ) : (
                      <div className="grid gap-2 sm:grid-cols-2">
                        {aiPrompts.map((prompt) => (
                          <button
                            key={prompt}
                            type="button"
                            onClick={() => insertBrainstormingPrompt(prompt)}
                            className="rounded-xl border border-[#e7d8a2] bg-white/80 p-3 text-left text-xs leading-5 text-[#4d4d4a] transition hover:border-[#d5b96d] hover:bg-[#fffdf5]"
                          >
                            {prompt}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>

            <aside className="hidden border-l border-[#deded8] bg-[#f3f3ef] xl:block">
              <CoachPanel
                suggestions={visibleSuggestions}
                accepted={accepted}
                onAccept={acceptSuggestion}
                onDismiss={dismissSuggestion}
                comment={comment}
                onOpenMethod={() => setLibraryOpen(true)}
                coachBasis={page.coachBasis}
                why={page.why}
                phaseLabel={phases[activePhase].title}
              />
            </aside>
          </div>
        </main>
      </div>

      <button
        onClick={() => setCoachOpen(true)}
        className="fixed bottom-5 right-5 flex items-center gap-2 rounded-full bg-[#2c302c] px-4 py-3 text-sm font-medium text-white shadow-lg xl:hidden"
      >
        <Sparkles size={17} />
        AI coach
        <span className="flex size-5 items-center justify-center rounded-full bg-[#d9a74b] text-[11px] text-[#282b27]">
          {visibleSuggestions.length}
        </span>
      </button>

      {coachOpen && (
        <div className="fixed inset-0 z-50 bg-black/30 xl:hidden">
          <button
            className="absolute inset-0"
            onClick={() => setCoachOpen(false)}
            aria-label="Close AI coach"
          />
          <div className="absolute inset-y-0 right-0 w-full max-w-[410px] overflow-y-auto bg-[#f3f3ef] shadow-2xl">
            <button
              className="icon-button absolute right-4 top-4 z-10"
              onClick={() => setCoachOpen(false)}
            >
              <X size={18} />
            </button>
            <CoachPanel
              suggestions={visibleSuggestions}
              accepted={accepted}
              onAccept={acceptSuggestion}
              onDismiss={dismissSuggestion}
              comment={comment}
              onOpenMethod={() => setLibraryOpen(true)}
              coachBasis={page.coachBasis}
              why={page.why}
              phaseLabel={phases[activePhase].title}
            />
          </div>
        </div>
      )}

      {libraryOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-[#1d211e]/40 p-3 backdrop-blur-[2px] sm:p-6">
          <button
            className="absolute inset-0"
            onClick={() => setLibraryOpen(false)}
            aria-label="Close methodology"
          />
          <div
            role="dialog"
            aria-modal="true"
            className="relative flex max-h-[90vh] w-full max-w-[1040px] flex-col overflow-hidden rounded-2xl border border-[#deded8] bg-[#f8f8f5] shadow-2xl"
          >
            <div className="flex items-start justify-between border-b border-[#deded8] bg-white px-5 py-5 sm:px-7">
              <div>
                <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.13em] text-[#4d846f]">
                  Book-based framework
                </div>
                <h2 className="text-xl font-semibold tracking-[-0.02em] sm:text-2xl">
                  UX design methodology
                </h2>
                <p className="mt-1.5 max-w-2xl text-xs leading-5 text-[#747770] sm:text-sm">
                  The book defines five phases. This tool intentionally supports only the first
                  three—the space where a designer frames, investigates, and develops ideas.
                </p>
              </div>
              <button className="icon-button shrink-0" onClick={() => setLibraryOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="overflow-y-auto p-4 sm:p-7">
              <div className="mb-6 flex items-center gap-2 overflow-x-auto pb-1">
                {phases.map((phase, index) => (
                  <div key={phase.title} className="flex shrink-0 items-center gap-2">
                    <div
                      className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${
                        index === 0
                          ? "border-[#8eae9f] bg-[#e3eee8] text-[#3f715d]"
                          : "border-[#d7d8d2] bg-white text-[#6c6f69]"
                      }`}
                    >
                      {String.fromCharCode(65 + index)}. {phase.title}
                    </div>
                    {index < phases.length - 1 && (
                      <ChevronRight size={14} className="text-[#b1b3ad]" />
                    )}
                  </div>
                ))}
              </div>

              <div className="mb-6 overflow-hidden rounded-xl border border-[#deded8] bg-white p-3">
                <img
                  src="/methodology-scope.png"
                  alt="The five phases of the UX methodology: Planning, Exploration, Ideation, Generation, and Evaluation."
                  className="h-auto w-full rounded-lg"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                {phases.map((phase, phaseIndex) => (
                  <section
                    key={phase.title}
                    className="rounded-xl border border-[#deded8] bg-white p-4"
                  >
                    <div className="mb-4 flex items-start justify-between gap-2">
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#92958e]">
                          Phase {String.fromCharCode(65 + phaseIndex)}
                        </div>
                        <h3 className="mt-0.5 text-sm font-semibold">{phase.title}</h3>
                      </div>
                      <span className="flex size-6 items-center justify-center rounded-full bg-[#f0f1ec] text-[10px] font-semibold text-[#70736c]">
                        {phase.steps.length}
                      </span>
                    </div>
                    <div className="space-y-1.5">
                      {phase.steps.map((method) => (
                        <button
                          key={method}
                          onClick={() => {
                            changePhase(phaseIndex);
                            setLibraryOpen(false);
                          }}
                          className={`w-full rounded-md px-2.5 py-2 text-left text-[11px] leading-4 transition ${
                            phaseIndex === activePhase
                              ? "bg-[#e7f0eb] font-semibold text-[#3f715d]"
                              : "bg-[#f7f7f4] text-[#5f625c] hover:bg-[#efefe9]"
                          }`}
                        >
                          {method}
                        </button>
                      ))}
                    </div>
                  </section>
                ))}
              </div>

              <div className="mt-5 flex flex-col gap-3 rounded-xl border border-[#deded8] bg-[#edeee9] p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <Clock3 size={17} className="mt-0.5 shrink-0 text-[#5d7f70]" />
                  <p className="text-xs leading-5 text-[#62655f]">
                    In scope: framing the project, exploring user needs, synthesizing evidence, and
                    brainstorming ideas. Out of scope: formalizing solutions and evaluating them.
                  </p>
                </div>
                <span className="shrink-0 text-[11px] font-semibold text-[#47715f]">
                  3 phases · 15 book methods
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {showComment && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-[#1d211e]/35 p-4 backdrop-blur-[2px]">
          <button
            className="absolute inset-0"
            onClick={() => setShowComment(false)}
            aria-label="Close dialog"
          />
          <div
            role="dialog"
            aria-modal="true"
            className="relative w-full max-w-[480px] rounded-2xl border border-[#deded8] bg-[#fbfbf9] p-6 shadow-2xl"
          >
            <button
              className="icon-button absolute right-4 top-4"
              onClick={() => setShowComment(false)}
            >
              <X size={18} />
            </button>
            <div className="mb-5 flex size-10 items-center justify-center rounded-xl bg-[#f8e8ba] text-[#936516]">
              <MessageCircle size={19} />
            </div>
            <h2 className="text-xl font-semibold tracking-[-0.02em]">Add a consideration</h2>
            <p className="mt-2 pr-5 text-sm leading-6 text-[#686b65]">
              Keep this thought visible as your project develops. You can revisit or resolve it when
              you have stronger evidence.
            </p>
            <label className="mt-5 block text-xs font-semibold text-[#565954]">
              Note for the team
            </label>
            <textarea
              autoFocus
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Write a note for your team…"
              className="mt-2 min-h-[110px] w-full resize-none rounded-lg border border-[#d9dad4] bg-white p-3 text-sm leading-6 outline-none focus:border-[#c19b54] focus:ring-3 focus:ring-[#f2e6cb]/60"
            />
            <div className="mt-5 flex justify-end gap-2">
              <button
                className="rounded-lg px-4 py-2 text-sm font-medium text-[#62655f] hover:bg-[#efefeb]"
                onClick={() => setShowComment(false)}
              >
                Cancel
              </button>
              <button
                onClick={saveComment}
                disabled={!comment.trim() || commentSaved}
                className="flex items-center gap-2 rounded-lg bg-[#282b27] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {commentSaved ? <Check size={16} /> : <MessageCircle size={15} />}
                {commentSaved ? "Comment added" : "Add comment"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CoachPanel({
  suggestions,
  accepted,
  onAccept,
  onDismiss,
  comment,
  onOpenMethod,
  coachBasis,
  why,
  phaseLabel,
}: {
  suggestions: Suggestion[];
  accepted: number[];
  onAccept: (suggestion: Suggestion) => void;
  onDismiss: (id: number) => void;
  comment: string;
  onOpenMethod: () => void;
  coachBasis: string;
  why: string;
  phaseLabel: string;
}) {
  return (
    <div className="px-5 py-7 sm:px-6">
      <div className="mb-7 flex items-start gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[#dfeae4] text-[#43715e]">
          <Sparkles size={19} />
        </div>
        <div>
          <h2 className="font-semibold tracking-[-0.01em]">AI coach</h2>
          <p className="mt-0.5 text-xs leading-5 text-[#777a74]">{coachBasis}</p>
        </div>
      </div>

      <div className="mb-5 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6e716b]">
          Ranked suggestions
        </span>
        <span className="text-[11px] text-[#989a94]">Most important first</span>
      </div>

      <div className="space-y-3">
        {suggestions.map((suggestion, index) => {
          const isAccepted = accepted.includes(suggestion.id);
          return (
            <div
              key={suggestion.id}
              className={`rounded-lg border border-[#deded7] border-l-[3px] p-4 ${
                suggestion.importance === "high" ? "ring-1 ring-[#d5b163]/50" : ""
              } ${typeStyles[suggestion.type].shell}`}
            >
              <div className="mb-3 flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-[#8c8f88]">#{index + 1}</span>
                  <span
                    className={`flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-bold uppercase tracking-[0.09em] ${typeStyles[suggestion.type].badge}`}
                  >
                    {suggestion.importance === "high" && (
                      <Star size={11} fill="currentColor" aria-hidden="true" />
                    )}
                    {suggestion.label}
                  </span>
                </div>
                <button
                  onClick={() => onDismiss(suggestion.id)}
                  className="text-[#a0a29c] transition hover:text-[#565954]"
                  aria-label="Dismiss suggestion"
                >
                  <X size={15} />
                </button>
              </div>
              <p className="text-[13px] leading-[1.55] text-[#4f524d]">{suggestion.text}</p>
              {suggestion.type === "consider" && comment && isAccepted && (
                <div className="mt-3 rounded-md bg-white/70 p-2.5 text-xs leading-5 text-[#686450]">
                  <span className="font-semibold">Team note:</span> {comment}
                </div>
              )}
              <button
                onClick={() => onAccept(suggestion)}
                disabled={isAccepted}
                className="mt-3.5 flex items-center gap-1.5 text-xs font-semibold text-[#4c514c] transition hover:text-black disabled:text-[#4d846f]"
              >
                {isAccepted ? <Check size={14} /> : <Plus size={14} />}
                {isAccepted ? "Applied" : suggestion.action}
              </button>
            </div>
          );
        })}
        {suggestions.length === 0 && (
          <div className="rounded-xl border border-dashed border-[#d5d6d0] p-6 text-center">
            <CheckCircle2 size={22} className="mx-auto mb-2 text-[#5f8d79]" />
            <p className="text-sm font-medium">All reviewed</p>
            <p className="mt-1 text-xs text-[#858781]">New suggestions will appear as you write.</p>
          </div>
        )}
      </div>

      <div className="mt-7 rounded-xl border border-[#d9dad4] bg-white/65 p-4">
        <div className="mb-2 flex items-center gap-2">
          <BookOpen size={15} className="text-[#5b816f]" />
          <span className="text-xs font-semibold">Why this matters</span>
        </div>
        <p className="text-xs leading-5 text-[#72756f]">{why}</p>
        <button onClick={onOpenMethod} className="mt-3 text-xs font-semibold text-[#47715f]">
          View supported methods
        </button>
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-[#deded8] pt-5 text-xs text-[#858781]">
        <span className="flex items-center gap-1.5">
          <Users size={14} />
          Visible to your team
        </span>
        <span className="flex items-center gap-1 font-medium text-[#5d605a]">
          <UserRound size={13} />
          {phaseLabel} active
        </span>
      </div>
    </div>
  );
}

export default App;
