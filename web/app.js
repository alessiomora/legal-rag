const state = {
  mode: "retrieve",
};

const form = document.querySelector("#query-form");
const queryInput = document.querySelector("#query-input");
const topKInput = document.querySelector("#top-k");
const submitButton = document.querySelector("#submit-button");
const queryLabel = document.querySelector("#query-label");
const statusBadge = document.querySelector("#status-badge");
const answerCard = document.querySelector("#answer-card");
const resultsList = document.querySelector("#results-list");
const tabs = document.querySelectorAll(".tab");
const exampleButtons = document.querySelectorAll("[data-example]");

function setMode(mode) {
  state.mode = mode;
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.mode === mode));
  queryLabel.textContent = mode === "ask" ? "Question" : "Query";
  submitButton.textContent = mode === "ask" ? "Ask with citations" : "Retrieve evidence";
}

function setStatus(text, isError = false) {
  statusBadge.textContent = text;
  statusBadge.classList.toggle("error", isError);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function chunkCard(chunk, index) {
  const article = chunk.article || "Unknown article";
  const section = chunk.section ? ` - ${chunk.section}` : "";
  return `
    <article class="chunk-card">
      <div class="chunk-meta">
        <span class="pill">#${index + 1}</span>
        <span class="pill">${escapeHtml(article)}${escapeHtml(section)}</span>
        <span class="pill">score ${Number(chunk.score).toFixed(3)}</span>
        <span class="pill">${escapeHtml(chunk.chunk_id)}</span>
      </div>
      <h3>${escapeHtml(article)}${escapeHtml(section)}</h3>
      <p class="chunk-text">${escapeHtml(chunk.text)}</p>
    </article>
  `;
}

function renderRetrieve(data) {
  answerCard.classList.add("hidden");
  if (!data.results.length) {
    resultsList.innerHTML = `<div class="empty-state">No chunks returned.</div>`;
    return;
  }
  resultsList.innerHTML = data.results.map(chunkCard).join("");
}

function renderAsk(data) {
  answerCard.classList.remove("hidden");
  answerCard.innerHTML = `
    <h3>Answer</h3>
    <p>${escapeHtml(data.answer)}</p>
  `;

  if (!data.citations.length) {
    resultsList.innerHTML = `<div class="empty-state">No citations returned.</div>`;
    return;
  }

  resultsList.innerHTML = data.citations
    .map(
      (citation, index) => `
        <article class="chunk-card">
          <div class="chunk-meta">
            <span class="pill">Citation ${index + 1}</span>
            <span class="pill">${escapeHtml(citation.article || "Unknown article")}</span>
            <span class="pill">score ${Number(citation.score).toFixed(3)}</span>
          </div>
          <h3>${escapeHtml(citation.article || citation.chunk_id)}</h3>
          <p class="chunk-text">${escapeHtml(citation.chunk_id)}</p>
        </article>
      `,
    )
    .join("");
}

async function sendRequest(event) {
  event.preventDefault();
  const text = queryInput.value.trim();
  if (!text) return;

  const topK = Number(topKInput.value || 5);
  const endpoint = state.mode === "ask" ? "/ask" : "/retrieve";
  const payload =
    state.mode === "ask" ? { question: text, top_k: topK } : { query: text, top_k: topK };

  submitButton.disabled = true;
  setStatus("Working");
  answerCard.classList.add("hidden");
  resultsList.innerHTML = `<div class="empty-state">Waiting for ${endpoint}...</div>`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `Request failed with status ${response.status}`);
    }

    if (state.mode === "ask") {
      renderAsk(data);
    } else {
      renderRetrieve(data);
    }
    setStatus("Done");
  } catch (error) {
    answerCard.classList.add("hidden");
    resultsList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    setStatus("Error", true);
  } finally {
    submitButton.disabled = false;
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => setMode(tab.dataset.mode));
});

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    queryInput.value = button.dataset.example;
    queryInput.focus();
  });
});

form.addEventListener("submit", sendRequest);
setMode("retrieve");
resultsList.innerHTML = `<div class="empty-state">Submit a GDPR query to inspect retrieved evidence.</div>`;
