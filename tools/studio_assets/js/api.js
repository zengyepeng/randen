/* ===== API Layer ===== */

export async function api(path, options = {}) {
  const headers = { Accept: "application/json", ...(options.headers || {}) };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    headers["X-Randen-Studio"] = "1";
  }
  const response = await fetch(path, { ...options, headers });
  const contentType = response.headers.get("Content-Type") || "";
  const body = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const error = new Error(body?.error || `请求失败 (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return body;
}

export async function loadWorkspace() {
  const data = await api("/api/workspace");
  return data;
}

export async function saveDocumentAPI(path, content, version) {
  return api("/api/document", {
    method: "PUT",
    body: JSON.stringify({ path, content, version }),
  });
}

export async function saveFocusAPI(goal, mustKeep, mustAvoid, notes) {
  return api("/api/focus", {
    method: "POST",
    body: JSON.stringify({ goal, must_keep: mustKeep, must_avoid: mustAvoid, notes }),
  });
}

export async function saveModelAPI(provider, baseUrl, model, apiKey, apiFormat) {
  return api("/api/model", {
    method: "POST",
    body: JSON.stringify({
      provider,
      base_url: baseUrl,
      model,
      api_key: apiKey,
      api_format: apiFormat,
    }),
  });
}

export async function initializeProjectAPI(novelId, title) {
  return api("/api/project/init", {
    method: "POST",
    body: JSON.stringify({ novel_id: novelId, title }),
  });
}

export async function getDocumentAPI(path) {
  return api(`/api/document?path=${encodeURIComponent(path)}`);
}

export async function syncProjectAPI() {
  return api("/api/sync", { method: "POST", body: "{}" });
}

export async function inspectContextAPI(chapter) {
  return api(`/api/context?chapter=${encodeURIComponent(chapter)}`);
}

export async function importTextAPI(filename, content, arcId, startNumber, force) {
  return api("/api/import", {
    method: "POST",
    body: JSON.stringify({ filename, content, arc_id: arcId, start_number: startNumber, force }),
  });
}

export async function createDocumentAPI(kind, name, description) {
  return api("/api/document/create", {
    method: "POST",
    body: JSON.stringify({ kind, name, description }),
  });
}

export async function submitChatAPI(agent, message) {
  return api("/api/chat", {
    method: "POST",
    body: JSON.stringify({ agent, message }),
  });
}

export async function loadContinuityAPI() {
  return api("/api/continuity");
}

export async function createForeshadowingAPI(nodeData) {
  return api("/api/foreshadowing", {
    method: "POST",
    body: JSON.stringify({ action: "create", ...nodeData }),
  });
}

export async function extractSourceAPI(sourceId, focus, content) {
  return api("/api/source", {
    method: "POST",
    body: JSON.stringify({ action: "extract", source_id: sourceId, focus, content }),
  });
}

export async function runSourceActionAPI(action, sourceId) {
  return api("/api/source", {
    method: "POST",
    body: JSON.stringify({ action, source_id: sourceId, target: "all" }),
  });
}

export async function runWriterAPI(guidance, targetWords) {
  return api("/api/write", {
    method: "POST",
    body: JSON.stringify({ guidance, target_words: targetWords }),
  });
}

export async function runReviewAPI(path) {
  return api("/api/review", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
}
