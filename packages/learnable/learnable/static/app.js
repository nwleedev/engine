async function loadSessions() {
  const status = document.getElementById("status");
  const sessions = document.getElementById("sessions");
  const material = document.getElementById("material");
  const response = await fetch("/api/sessions");
  const payload = await response.json();
  sessions.textContent = "";
  for (const session of payload.sessions) {
    const button = document.createElement("button");
    button.textContent = session.title;
    button.addEventListener("click", async () => {
      const treeResponse = await fetch(`/api/materials/tree?learnable_session_id=${encodeURIComponent(session.learnable_session_id)}`);
      const tree = await treeResponse.json();
      const root = tree.tree.root_node_id;
      const nodeResponse = await fetch(`/api/materials/node?learnable_session_id=${encodeURIComponent(session.learnable_session_id)}&node_id=${encodeURIComponent(root)}`);
      const node = await nodeResponse.json();
      status.textContent = node.material.title;
      material.innerHTML = "";
      const pre = document.createElement("pre");
      pre.textContent = node.markdown;
      material.appendChild(pre);
    });
    sessions.appendChild(button);
  }
  status.textContent = payload.sessions.length ? "Select a material" : "No materials found";
}

loadSessions().catch(() => {
  document.getElementById("status").textContent = "Unable to load local materials";
});
