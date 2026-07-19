/* ===== Router: View Switching & Navigation ===== */

import { state, setView, setDocument } from "./state.js";
import { $, $$, labels } from "./utils.js";
import { getDocumentAPI, loadContinuityAPI } from "./api.js";
import { renderDocumentList } from "./views/dashboard.js";
import { updateEditorCount } from "./views/editor.js";
import { renderContinuity } from "./views/continuity.js";

export function documentGroup(path) {
  if (path.startsWith("data/manuscript/")) return "chapters";
  if (path.startsWith("src/characters/")) return "characters";
  if (path.startsWith("src/world/")) return "world";
  return "story";
}

export function switchView(view, pushHistory = true) {
  setView(view);
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));

  const dashboard = view === "dashboard";
  const documentView = ["chapters", "story", "characters", "world"].includes(view);

  const dashView = $("#dashboard-view");
  const editorView = $("#editor-view");
  const agentsView = $("#agents-view");
  const continuityView = $("#continuity-view");
  const toolsView = $("#tools-view");
  const emotionView = $("#emotion-view");

  if (dashView) dashView.hidden = !dashboard;
  if (editorView) editorView.hidden = !documentView;
  if (agentsView) agentsView.hidden = view !== "agents";
  if (continuityView) continuityView.hidden = view !== "continuity";
  if (toolsView) toolsView.hidden = view !== "tools";
  if (emotionView) emotionView.hidden = view !== "emotion";

  renderDocumentList(dashboard || !documentView ? "chapters" : view);

  if (documentView && (!state.document || documentGroup(state.document.path) !== view)) {
    const first = state.workspace?.documents?.[view]?.[0];
    if (first) openDocument(first.path, false);
  }

  if (view === "continuity") loadContinuityView();
  if (pushHistory) {
    const url = dashboard ? "/" : `/#${encodeURIComponent(view)}`;
    history.pushState({ view }, "", url);
  }
}

export async function openDocument(path, pushHistory) {
  const { showToast } = await import("./utils.js");
  if (state.dirty && !window.confirm("当前文档尚未保存，仍要离开吗？")) return;
  try {
    const doc = await getDocumentAPI(path);
    setDocument(doc);
    state.dirty = false;
    const group = documentGroup(path);
    setView(group);
    $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === group));

    const dashView = $("#dashboard-view");
    const editorView = $("#editor-view");
    const agentsView = $("#agents-view");
    const continuityView = $("#continuity-view");
    const toolsView = $("#tools-view");
    const emotionView = $("#emotion-view");

    if (dashView) dashView.hidden = true;
    if (editorView) editorView.hidden = false;
    if (agentsView) agentsView.hidden = true;
    if (continuityView) continuityView.hidden = true;
    if (toolsView) toolsView.hidden = true;
    if (emotionView) emotionView.hidden = true;

    const editorPath = $("#editor-path");
    const editorTitle = $("#editor-title");
    const docEditor = $("#document-editor");
    const reviewBtn = $("#review-document");

    if (editorPath) editorPath.textContent = doc.path;
    if (editorTitle) editorTitle.value = doc.title;
    if (docEditor) docEditor.value = doc.content;
    if (reviewBtn) reviewBtn.hidden = group !== "chapters" || !state.workspace?.model?.configured;

    updateEditorCount();
    await import("./utils.js").then(m => m.setSaveState("已保存", false));
    renderDocumentList(group);

    if (pushHistory) {
      history.pushState({ path }, "", `/#doc=${encodeURIComponent(path)}`);
    }
    if (docEditor) docEditor.focus();
  } catch (error) {
    showToast(error.message, true);
  }
}

export async function routeFromLocation() {
  const hash = decodeURIComponent(location.hash.slice(1));
  const validViews = ["chapters", "story", "characters", "world", "agents", "continuity", "tools", "emotion"];
  if (hash.startsWith("doc=")) {
    await openDocument(hash.slice(4), false);
  } else if (validViews.includes(hash)) {
    switchView(hash, false);
  } else {
    switchView("dashboard", false);
  }
}

async function loadContinuityView() {
  const truthEl = $("#truth-current");
  if (truthEl) truthEl.textContent = "载入中…";
  try {
    state.continuity = await loadContinuityAPI();
    renderContinuity();
  } catch (error) {
    if (truthEl) truthEl.textContent = error.message;
    const { showToast } = await import("./utils.js");
    showToast(error.message, true);
  }
}
