type Citation = {
  id: number;
  source: string;
  title?: string | null;
  text?: string;
};

type QueryResponse = {
  overview?: string;
  self_help?: string;
  therapist?: string;
  citations?: Citation[];
  debug?: Record<string, unknown>;
};

type ApiErrorBody = {
  detail?: string | Record<string, unknown> | Array<Record<string, unknown>>;
};

const askBtn = mustGetById<HTMLButtonElement>("askBtn");
const queryEl = mustGetById<HTMLTextAreaElement>("query");
const statusEl = mustGetById<HTMLSpanElement>("status");
const resultEl = mustGetById<HTMLElement>("result");
const errorEl = mustGetById<HTMLElement>("error");
const overviewEl = mustGetById<HTMLElement>("overview");
const selfHelpEl = mustGetById<HTMLElement>("selfHelp");
const therapistEl = mustGetById<HTMLElement>("therapist");
const answerSkeletonEl = mustGetById<HTMLElement>("answerSkeleton");
const citationsEl = mustGetById<HTMLUListElement>("citations");
const debugEl = mustGetById<HTMLElement>("debug");
let requestInFlight = false;

function mustGetById<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!(node instanceof HTMLElement)) {
    throw new Error(`Missing required element: #${id}`);
  }
  return node as T;
}

function setLoading(isLoading: boolean): void {
  requestInFlight = isLoading;
  document.body.classList.toggle("is-loading", isLoading);
  askBtn.disabled = isLoading;
  if (isLoading) {
    statusEl.textContent = "Выполняется запрос...";
    statusEl.classList.add("is-loading");
    statusEl.setAttribute("aria-busy", "true");
  } else {
    statusEl.textContent = "";
    statusEl.classList.remove("is-loading");
    statusEl.removeAttribute("aria-busy");
  }
  answerSkeletonEl.classList.toggle("hidden", !isLoading);
  overviewEl.classList.toggle("hidden", isLoading);
  selfHelpEl.classList.toggle("hidden", isLoading);
  therapistEl.classList.toggle("hidden", isLoading);
}

function showError(message: string): void {
  errorEl.classList.remove("hidden");
  errorEl.textContent = message;
  resultEl.classList.add("hidden");
}

function hideError(): void {
  errorEl.classList.add("hidden");
  errorEl.textContent = "";
}

function renderCitations(citations: Citation[]): void {
  citationsEl.innerHTML = "";
  for (const item of citations) {
    const li = document.createElement("li");
    const source = document.createElement("div");
    source.className = "citation-source";
    source.textContent = `${item.id}. ${item.source}`;
    li.appendChild(source);

    if (item.title) {
      const title = document.createElement("div");
      title.className = "citation-title";
      title.textContent = item.title;
      li.appendChild(title);
    }

    if (item.text) {
      const preview = document.createElement("div");
      preview.className = "citation-text";
      preview.textContent = item.text.slice(0, 240);
      li.appendChild(preview);
    }

    citationsEl.appendChild(li);
  }
}

function parseApiError(body: unknown): string {
  if (!body || typeof body !== "object") {
    return "Неизвестная ошибка API";
  }
  const detail = (body as ApiErrorBody).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (detail) {
    return JSON.stringify(detail, null, 2);
  }
  return "Неизвестная ошибка API";
}

async function ask(): Promise<void> {
  if (requestInFlight) {
    return;
  }
  const query = queryEl.value.trim();
  if (query.length < 3) {
    showError("Введите запрос минимум из 3 символов.");
    return;
  }

  setLoading(true);
  hideError();
  overviewEl.textContent = "";
  selfHelpEl.textContent = "";
  therapistEl.textContent = "";
  citationsEl.innerHTML = "";
  debugEl.textContent = "";
  resultEl.classList.remove("hidden");

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const rawText = await response.text();
    let data: unknown = {};
    if (rawText) {
      try {
        data = JSON.parse(rawText);
      } catch {
        if (!response.ok) {
          throw new Error(`Ошибка API (${response.status}): ${rawText}`);
        }
      }
    }

    if (!response.ok) {
      throw new Error(parseApiError(data));
    }

    const payload = data as QueryResponse;
    overviewEl.textContent = payload.overview || "(Пустой ответ)";
    selfHelpEl.textContent = payload.self_help || "(Пустой ответ)";
    therapistEl.textContent = payload.therapist || "(Пустой ответ)";
    renderCitations(payload.citations ?? []);
    debugEl.textContent = JSON.stringify(payload.debug ?? {}, null, 2);
    resultEl.classList.remove("hidden");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    showError(message);
  } finally {
    setLoading(false);
  }
}

askBtn.addEventListener("click", () => {
  void ask();
});

queryEl.addEventListener("keydown", (event: KeyboardEvent) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    void ask();
  }
});
