"use strict";
const askBtn = mustGetById("askBtn");
const queryEl = mustGetById("query");
const statusEl = mustGetById("status");
const resultEl = mustGetById("result");
const errorEl = mustGetById("error");
const overviewEl = mustGetById("overview");
const selfHelpEl = mustGetById("selfHelp");
const therapistEl = mustGetById("therapist");
const answerSkeletonEl = mustGetById("answerSkeleton");
const citationsEl = mustGetById("citations");
const debugEl = mustGetById("debug");
let requestInFlight = false;
function mustGetById(id) {
    const node = document.getElementById(id);
    if (!(node instanceof HTMLElement)) {
        throw new Error(`Missing required element: #${id}`);
    }
    return node;
}
function setLoading(isLoading) {
    requestInFlight = isLoading;
    document.body.classList.toggle("is-loading", isLoading);
    askBtn.disabled = isLoading;
    if (isLoading) {
        statusEl.textContent = "Выполняется запрос...";
        statusEl.classList.add("is-loading");
        statusEl.setAttribute("aria-busy", "true");
    }
    else {
        statusEl.textContent = "";
        statusEl.classList.remove("is-loading");
        statusEl.removeAttribute("aria-busy");
    }
    answerSkeletonEl.classList.toggle("hidden", !isLoading);
    overviewEl.classList.toggle("hidden", isLoading);
    selfHelpEl.classList.toggle("hidden", isLoading);
    therapistEl.classList.toggle("hidden", isLoading);
}
function showError(message) {
    errorEl.classList.remove("hidden");
    errorEl.textContent = message;
    resultEl.classList.add("hidden");
}
function hideError() {
    errorEl.classList.add("hidden");
    errorEl.textContent = "";
}
function renderCitations(citations) {
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
function parseApiError(body) {
    if (!body || typeof body !== "object") {
        return "Неизвестная ошибка API";
    }
    const detail = body.detail;
    if (typeof detail === "string") {
        return detail;
    }
    if (detail) {
        return JSON.stringify(detail, null, 2);
    }
    return "Неизвестная ошибка API";
}
async function ask() {
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
        let data = {};
        if (rawText) {
            try {
                data = JSON.parse(rawText);
            }
            catch {
                if (!response.ok) {
                    throw new Error(`Ошибка API (${response.status}): ${rawText}`);
                }
            }
        }
        if (!response.ok) {
            throw new Error(parseApiError(data));
        }
        const payload = data;
        overviewEl.textContent = payload.overview || "(Пустой ответ)";
        selfHelpEl.textContent = payload.self_help || "(Пустой ответ)";
        therapistEl.textContent = payload.therapist || "(Пустой ответ)";
        renderCitations(payload.citations ?? []);
        debugEl.textContent = JSON.stringify(payload.debug ?? {}, null, 2);
        resultEl.classList.remove("hidden");
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        showError(message);
    }
    finally {
        setLoading(false);
    }
}
askBtn.addEventListener("click", () => {
    void ask();
});
queryEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        void ask();
    }
});
