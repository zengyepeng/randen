/* ===== Randen Studio — Application Entry ===== */

import { state } from "./state.js";
import { $, $$, showToast, setSaveState } from "./utils.js";
import { loadWorkspace as loadWorkspaceAPI } from "./api.js";
import { switchView, openDocument, routeFromLocation } from "./router.js";
import { renderWorkspace } from "./views/dashboard.js";
import { initCreationWizard, initAIAssistants } from "./views/tools.js";
import { updateEditorCount } from "./views/editor.js";
import { chooseAgent, appendChatMessage } from "./views/agents.js";
import { renderContinuity } from "./views/continuity.js";
import { renderEmotionDashboard } from "./views/emotion.js";
import {
  saveDocument,
  saveFocus,
  saveModel,
  initializeProject,
  runSync,
  inspectContext,
  importText,
  createDocument as createDocumentAction,
  submitChat,
  createForeshadowing,
  extractSource,
  runWriter,
} from "./actions.js";
import { runReview } from "./actions-review.js";

/* ---- Boot ---- */
async function loadWorkspace() {
  state.workspace = await loadWorkspaceAPI();
  renderWorkspace();
  initCreationWizard();
  initAIAssistants();
  const app = document.querySelector("#app");
  if (app) app.setAttribute("aria-busy", "false");
  if (!state.workspace.initialized) {
    const projectDialog = $("#project-dialog");
    if (projectDialog && !projectDialog.open) projectDialog.showModal();
  }
}

async function boot() {
  const storedTheme = localStorage.getItem("randen-theme");
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(storedTheme || (systemDark ? "dark" : "light"));
  bindEvents();
  // Always release busy state after bindEvents — don't wait for workspace
  const app = document.querySelector("#app");
  if (app) app.setAttribute("aria-busy", "false");
  try {
    await loadWorkspace();
    await routeFromLocation();
  } catch (error) {
    showToast(error.message, true);
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const logo = $(".brand-logo");
  if (logo) logo.src = theme === "dark" ? "/brand/logo-dark.svg" : "/brand/logo.svg";
  localStorage.setItem("randen-theme", theme);
}

/* ---- Event Bindings ---- */
function bindEvents() {
  // Navigation
  $$(".nav-item").forEach((btn) => btn.addEventListener("click", () => switchView(btn.dataset.view)));
  $$("[data-switch-view]").forEach((btn) =>
    btn.addEventListener("click", () => switchView(btn.dataset.switchView))
  );

  // Editor
  const docEditor = $("#document-editor");
  if (docEditor) {
    docEditor.addEventListener("input", () => {
      state.dirty = true;
      setSaveState("未保存", true);
      updateEditorCount();
    });
  }
  const saveBtn = $("#save-document");
  if (saveBtn) saveBtn.addEventListener("click", saveDocument);
  const reviewBtn = $("#review-document");
  if (reviewBtn) reviewBtn.addEventListener("click", runReview);
  const reloadBtn = $("#reload-document");
  if (reloadBtn) reloadBtn.addEventListener("click", () => {
    if (state.document) openDocument(state.document.path, false);
  });

  // Focus
  const focusForm = $("#focus-form");
  if (focusForm) focusForm.addEventListener("submit", saveFocus);

  // Model
  const modelState = $("#model-state");
  if (modelState) modelState.addEventListener("click", () => $("#model-dialog")?.showModal());
  $$("#model-close, #model-cancel").forEach((el) =>
    el.addEventListener("click", () => $("#model-dialog")?.close())
  );
  const modelForm = $("#model-form");
  if (modelForm) modelForm.addEventListener("submit", saveModel);

  // Project
  const projectForm = $("#project-form");
  if (projectForm) projectForm.addEventListener("submit", initializeProject);
  const projectDialog = $("#project-dialog");
  if (projectDialog) {
    projectDialog.addEventListener("cancel", (event) => {
      if (!state.workspace?.initialized) event.preventDefault();
    });
  }

  // Write
  const writeOpen = $("#write-open");
  if (writeOpen) writeOpen.addEventListener("click", () => $("#write-dialog")?.showModal());
  $$("#write-close, #write-cancel").forEach((el) =>
    el.addEventListener("click", () => $("#write-dialog")?.close())
  );
  const writeForm = $("#write-form");
  if (writeForm) writeForm.addEventListener("submit", runWriter);

  // Review dialog
  const reviewClose = $("#review-close");
  if (reviewClose) reviewClose.addEventListener("click", () => $("#review-dialog")?.close());

  // Tools
  const syncBtn = $("#sync-project");
  if (syncBtn) syncBtn.addEventListener("click", runSync);
  const contextForm = $("#context-form");
  if (contextForm) contextForm.addEventListener("submit", inspectContext);
  const importForm = $("#import-form");
  if (importForm) importForm.addEventListener("submit", importText);
  const createForm = $("#create-document-form");
  if (createForm) createForm.addEventListener("submit", createDocumentAction);

  // Chat
  const chatForm = $("#chat-form");
  if (chatForm) chatForm.addEventListener("submit", submitChat);
  $$("[data-agent]").forEach((btn) => btn.addEventListener("click", () => chooseAgent(btn.dataset.agent)));

  // Continuity
  const contRefresh = $("#continuity-refresh");
  if (contRefresh) {
    contRefresh.addEventListener("click", async () => {
      const { loadContinuityAPI } = await import("./api.js");
      state.continuity = await loadContinuityAPI();
      renderContinuity();
    });
  }
  const foreshadowForm = $("#foreshadow-form");
  if (foreshadowForm) foreshadowForm.addEventListener("submit", createForeshadowing);

  // Source
  const sourceForm = $("#source-form");
  if (sourceForm) sourceForm.addEventListener("submit", extractSource);
  const sourceFile = $("#source-file");
  if (sourceFile) {
    sourceFile.addEventListener("change", async (event) => {
      const file = event.target.files[0];
      const contentEl = $("#source-content");
      if (file && contentEl) contentEl.value = await file.text();
    });
  }

  // Inspector
  const inspToggle = $("#inspector-toggle");
  if (inspToggle) inspToggle.addEventListener("click", () => toggleInspector(true));
  const inspClose = $("#inspector-close");
  if (inspClose) inspClose.addEventListener("click", () => toggleInspector(false));

  // Theme
  const themeToggle = $("#theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
    });
  }

  // Sidebar hamburger
  const sidebarToggle = $("#sidebar-toggle");
  const sidebarBody = $("#sidebar-body");
  if (sidebarToggle && sidebarBody) {
    sidebarToggle.addEventListener("click", () => {
      const expanded = sidebarToggle.getAttribute("aria-expanded") === "true";
      sidebarToggle.setAttribute("aria-expanded", String(!expanded));
      sidebarBody.classList.toggle("open", !expanded);
    });
  }

  // Emotion view render on switch
  $$('[data-view="emotion"]').forEach((btn) => {
    btn.addEventListener("click", () => {
      switchView("emotion");
      renderEmotionDashboard();
    });
  });

  // Keyboard
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      saveDocument();
    }
    if (event.key === "Escape") toggleInspector(false);
  });

  window.addEventListener("beforeunload", (event) => {
    if (state.dirty) event.preventDefault();
  });
  window.addEventListener("popstate", routeFromLocation);
}

function toggleInspector(open) {
  const inspector = $("#inspector");
  if (inspector) inspector.classList.toggle("open", open);
  const toggleBtn = $("#inspector-toggle");
  if (toggleBtn) toggleBtn.setAttribute("aria-expanded", String(open));
}

// Start
boot();
