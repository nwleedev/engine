const state = {
  sessions: [],
  activeSessionId: null,
  activeTree: null,
};

const elements = {
  sessions: document.getElementById("sessions"),
  sessionCount: document.getElementById("session-count"),
  serverState: document.getElementById("server-state"),
  localStatus: document.getElementById("local-status"),
  readerKicker: document.getElementById("reader-kicker"),
  title: document.getElementById("material-title"),
  created: document.getElementById("material-created"),
  runtime: document.getElementById("runtime-provenance"),
  hierarchy: document.getElementById("hierarchy"),
  empty: document.getElementById("empty-state"),
  material: document.getElementById("material"),
  sourceRefs: document.getElementById("source-refs"),
  prerequisites: document.getElementById("prerequisites"),
  related: document.getElementById("related-concepts"),
};

async function loadSessions() {
  setServerState("Checking", false);
  const statusResponse = await fetchJson("/api/status");
  setServerState(statusResponse.schema_version === "missing" ? "No store" : "Ready", false);

  const payload = await fetchJson("/api/sessions");
  state.sessions = payload.sessions || [];
  elements.sessionCount.textContent = `${state.sessions.length} sessions`;
  renderSessions();

  if (state.sessions.length === 0) {
    showEmptyState("No materials found");
    return;
  }

  await selectSession(state.sessions[0].learnable_session_id);
}

async function selectSession(sessionId) {
  state.activeSessionId = sessionId;
  renderSessions();

  const treePayload = await fetchJson(`/api/materials/tree?learnable_session_id=${encodeURIComponent(sessionId)}`);
  state.activeTree = treePayload.tree;
  await selectNode(sessionId, state.activeTree.root_node_id);
}

async function selectNode(sessionId, nodeId) {
  const payload = await fetchJson(`/api/materials/node?learnable_session_id=${encodeURIComponent(sessionId)}&node_id=${encodeURIComponent(nodeId)}`);
  renderMaterial(payload);
}

async function fetchJson(path) {
  const response = await fetch(path, { headers: { "Accept": "application/json" } });
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`);
  }
  return response.json();
}

function renderSessions() {
  elements.sessions.textContent = "";
  for (const session of state.sessions) {
    const button = document.createElement("button");
    button.className = "session-button";
    button.type = "button";
    button.setAttribute("aria-current", session.learnable_session_id === state.activeSessionId ? "true" : "false");
    button.addEventListener("click", () => {
      selectSession(session.learnable_session_id).catch(showError);
    });

    const title = document.createElement("span");
    title.className = "session-title";
    title.textContent = session.title || "Untitled material";
    const meta = document.createElement("span");
    meta.className = "session-meta";
    meta.textContent = formatDate(session.updated_at || session.created_at);
    button.append(title, meta);
    elements.sessions.appendChild(button);
  }
}

function renderMaterial(payload) {
  const material = payload.material || {};
  elements.empty.hidden = true;
  elements.material.hidden = false;
  elements.readerKicker.textContent = material.parent_node_id ? "Child material" : "Root material";
  elements.title.textContent = material.title || "Untitled material";
  elements.created.textContent = `Created ${formatDate(material.created_at)}`;
  elements.runtime.textContent = runtimeLabel(payload.runtime_provenance);
  elements.hierarchy.textContent = hierarchyLabel(payload);
  elements.material.replaceChildren(...markdownNodes(payload.markdown || ""));
  renderList(elements.sourceRefs, sourceRefLabels(payload.source_refs), "No source refs");
  renderList(elements.prerequisites, extractPrerequisites(payload.markdown || ""), "No prerequisites detected");
  renderList(elements.related, relatedLabels(payload.child_node_ids), "No related child concepts");
}

function markdownNodes(markdown) {
  const fragment = document.createDocumentFragment();
  const lines = markdown.split(/\r?\n/);
  let list = null;
  for (const line of lines) {
    if (line.startsWith("### ")) {
      list = null;
      fragment.appendChild(heading("h3", line.slice(4)));
    } else if (line.startsWith("## ")) {
      list = null;
      fragment.appendChild(heading("h2", line.slice(3)));
    } else if (line.startsWith("# ")) {
      list = null;
      fragment.appendChild(heading("h1", line.slice(2)));
    } else if (line.startsWith("- ")) {
      if (!list) {
        list = document.createElement("ul");
        fragment.appendChild(list);
      }
      const item = document.createElement("li");
      item.textContent = line.slice(2);
      list.appendChild(item);
    } else if (line.trim() === "") {
      list = null;
    } else {
      list = null;
      const paragraph = document.createElement("p");
      paragraph.textContent = line;
      fragment.appendChild(paragraph);
    }
  }
  return [...fragment.childNodes];
}

function heading(level, text) {
  const node = document.createElement(level);
  node.textContent = text;
  return node;
}

function renderList(target, values, emptyText) {
  target.textContent = "";
  const list = values.length ? values : [emptyText];
  for (const value of list) {
    const item = document.createElement("li");
    item.textContent = value;
    target.appendChild(item);
  }
}

function sourceRefLabels(sourceRefs) {
  if (!Array.isArray(sourceRefs)) {
    return [];
  }
  return sourceRefs.map((ref) => {
    if (typeof ref === "string") {
      return ref;
    }
    return ref.title || ref.source_id || ref.url || "Structured source";
  });
}

function extractPrerequisites(markdown) {
  const lines = markdown.split(/\r?\n/);
  const start = lines.findIndex((line) => /^#{1,3}\s+prerequisites\b/i.test(line));
  if (start === -1) {
    return [];
  }
  const values = [];
  for (const line of lines.slice(start + 1)) {
    if (/^#{1,3}\s+/.test(line)) {
      break;
    }
    if (line.startsWith("- ")) {
      values.push(line.slice(2));
    }
  }
  return values;
}

function relatedLabels(childNodeIds) {
  if (!Array.isArray(childNodeIds)) {
    return [];
  }
  return childNodeIds.map((nodeId) => `Child node ${nodeId}`);
}

function hierarchyLabel(payload) {
  const material = payload.material || {};
  const parent = payload.parent_node_id || material.parent_node_id;
  return parent ? `Parent ${parent} / Node ${material.node_id}` : `Root node ${material.node_id || "unknown"}`;
}

function runtimeLabel(provenance) {
  const runtime = provenance && provenance.runtime ? provenance.runtime : "unknown";
  return `Runtime ${runtime}`;
}

function formatDate(value) {
  if (!value) {
    return "time unavailable";
  }
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function showEmptyState(message) {
  elements.empty.textContent = message;
  elements.empty.hidden = false;
  elements.material.hidden = true;
}

function showError(error) {
  setServerState("Error", true);
  showEmptyState("Unable to load local materials");
  elements.empty.classList.add("error-text");
  console.error(error);
}

function setServerState(text, isError) {
  elements.serverState.textContent = text;
  elements.localStatus.textContent = text;
  elements.localStatus.classList.toggle("error-text", isError);
}

loadSessions().catch(showError);
