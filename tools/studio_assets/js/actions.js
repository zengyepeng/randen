/* ===== Async Action Handlers ===== */

import { state } from "./state.js";
import { $, showToast, setSaveState, formatNumber } from "./utils.js";
import {
  loadWorkspace as loadWorkspaceAPI,
  saveDocumentAPI,
  saveFocusAPI,
  saveModelAPI,
  initializeProjectAPI,
  syncProjectAPI,
  inspectContextAPI,
  importTextAPI,
  createDocumentAPI,
  submitChatAPI,
  createForeshadowingAPI,
  extractSourceAPI,
  runWriterAPI,
} from "./api.js";
import { renderWorkspace } from "./views/dashboard.js";
import { appendChatMessage } from "./views/agents.js";
import { renderContinuity } from "./views/continuity.js";

/* ---- Document ---- */
export async function saveDocument() {
  if (!state.document || !state.dirty || state.saving) return;
  state.saving = true;
  setSaveState("保存中", true);
  try {
    const docEditor = $("#document-editor");
    const saved = await saveDocumentAPI(
      state.document.path,
      docEditor ? docEditor.value : "",
      state.document.version
    );
    state.document = saved;
    state.dirty = false;
    setSaveState("已保存", false);
    showToast("文档已保存");
    state.workspace = await loadWorkspaceAPI();
    renderWorkspace();
  } catch (error) {
    setSaveState("保存失败", true);
    showToast(error.message, true);
  } finally {
    state.saving = false;
    const saveBtn = $("#save-document");
    if (saveBtn) saveBtn.disabled = !state.dirty;
  }
}

/* ---- Focus ---- */
export async function saveFocus(event) {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button[type=submit]");
  if (button) button.disabled = true;
  try {
    state.workspace = await saveFocusAPI(
      $("#focus-goal")?.value || "",
      ($("#focus-keep")?.value || "").split("\n"),
      ($("#focus-avoid")?.value || "").split("\n"),
      ($("#focus-notes")?.value || "").split("\n")
    );
    renderWorkspace();
    showToast("创作罗盘已更新");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    if (button) button.disabled = false;
  }
}

/* ---- Model ---- */
export async function saveModel(event) {
  event.preventDefault();
  const submit = $("#model-submit");
  const progress = $("#model-progress");
  if (submit) submit.disabled = true;
  if (progress) progress.textContent = "正在应用模型配置…";
  try {
    state.workspace = await saveModelAPI(
      $("#model-provider")?.value || "openai",
      ($("#model-base-url")?.value || "").trim(),
      ($("#model-name")?.value || "").trim(),
      ($("#model-api-key")?.value || "").trim(),
      $("#model-api-format")?.value || "chat"
    );
    const apiKeyEl = $("#model-api-key");
    if (apiKeyEl) apiKeyEl.value = "";
    renderWorkspace();
    $("#model-dialog")?.close();
    showToast(`模型已切换为 ${state.workspace.model.name}`);
  } catch (error) {
    if (progress) progress.textContent = error.message;
  } finally {
    if (submit) submit.disabled = false;
  }
}

/* ---- Project Init ---- */
export async function initializeProject(event) {
  event.preventDefault();
  const submit = $("#project-submit");
  const progress = $("#project-progress");
  if (submit) submit.disabled = true;
  if (progress) progress.textContent = "正在创建小说目录、真源和运行态…";
  try {
    state.workspace = await initializeProjectAPI(
      ($("#project-id")?.value || "").trim(),
      ($("#project-title")?.value || "").trim()
    );
    renderWorkspace();
    $("#project-dialog")?.close();
    showToast("小说工作区已创建");
  } catch (error) {
    if (progress) progress.textContent = error.message;
  } finally {
    if (submit) submit.disabled = false;
  }
}

/* ---- Tools ---- */
export async function runSync() {
  const button = $("#sync-project");
  const statusEl = $("#sync-status");
  if (button) button.disabled = true;
  if (statusEl) statusEl.textContent = "正在同步大纲与角色卡…";
  try {
    const payload = await syncProjectAPI();
    state.workspace = payload.workspace;
    renderWorkspace();
    showToast("src 与 data 已同步");
  } catch (error) {
    if (statusEl) statusEl.textContent = error.message;
    showToast(error.message, true);
  } finally {
    if (button) button.disabled = false;
  }
}

export async function inspectContext(event) {
  event.preventDefault();
  const chapter = ($("#context-chapter")?.value || "").trim() || "next";
  const metaEl = $("#context-meta");
  const previewEl = $("#context-preview");
  if (metaEl) metaEl.textContent = "正在组装上下文…";
  try {
    const payload = await inspectContextAPI(chapter);
    if (metaEl) metaEl.textContent = `${payload.chapter_id} · 目标 ${formatNumber(payload.target_words)} 字 · ${payload.characters.length} 位相关人物`;
    if (previewEl) previewEl.textContent = payload.markdown || "上下文为空";
  } catch (error) {
    if (metaEl) metaEl.textContent = error.message;
    showToast(error.message, true);
  }
}

export async function importText(event) {
  event.preventDefault();
  const fileEl = $("#import-file");
  const file = fileEl?.files[0];
  if (!file) return;
  const button = event.currentTarget.querySelector("button[type=submit]");
  const statusEl = $("#import-status");
  if (button) button.disabled = true;
  if (statusEl) statusEl.textContent = "正在解析并导入章节…";
  try {
    const payload = await importTextAPI(
      file.name,
      await file.text(),
      ($("#import-arc")?.value || "").trim(),
      $("#import-start")?.value || "",
      $("#import-force")?.checked || false
    );
    state.workspace = payload.workspace;
    renderWorkspace();
    if (statusEl) statusEl.textContent = `已导入 ${payload.imported.length} 章`;
    showToast(`已导入 ${payload.imported.length} 章正文`);
  } catch (error) {
    if (statusEl) statusEl.textContent = error.message;
    showToast(error.message, true);
  } finally {
    if (button) button.disabled = false;
  }
}

export async function createDocument(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form?.querySelector("button[type=submit]");
  const statusEl = $("#create-status");
  if (button) button.disabled = true;
  try {
    const payload = await createDocumentAPI(
      $("#create-kind")?.value || "character",
      ($("#create-name")?.value || "").trim(),
      ($("#create-description")?.value || "").trim()
    );
    state.workspace = payload.workspace;
    renderWorkspace();
    if (statusEl) statusEl.textContent = "文档已创建";
    form?.reset();
    const { openDocument } = await import("./router.js");
    await openDocument(payload.document.path, true);
  } catch (error) {
    if (statusEl) statusEl.textContent = error.message;
    showToast(error.message, true);
  } finally {
    if (button) button.disabled = false;
  }
}

/* ---- Chat ---- */
export async function submitChat(event) {
  event.preventDefault();
  const input = $("#chat-input");
  const message = input?.value.trim();
  if (!message) return;
  appendChatMessage("user", "你", message);
  if (input) input.value = "";
  const submitBtn = $("#chat-submit");
  const statusEl = $("#chat-status");
  if (submitBtn) submitBtn.disabled = true;
  if (statusEl) statusEl.textContent = `${state.agent === "goethe" ? "Goethe" : "Dante"} 正在读取项目并思考…`;
  try {
    const payload = await submitChatAPI(state.agent, message);
    appendChatMessage(
      "assistant",
      state.agent === "goethe" ? "Goethe" : "Dante",
      payload.content || "本轮已执行完成。"
    );
    state.workspace = payload.workspace;
    renderWorkspace();
  } catch (error) {
    appendChatMessage("assistant error", "系统", error.message);
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    if (statusEl) statusEl.textContent = "";
    if (input) input.focus();
  }
}

/* ---- Continuity ---- */
export async function createForeshadowing(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const payload = await createForeshadowingAPI({
      node_id: ($("#foreshadow-id")?.value || "").trim(),
      content: ($("#foreshadow-content")?.value || "").trim(),
      weight: Number($("#foreshadow-weight")?.value || 5),
      target_chapter: ($("#foreshadow-target")?.value || "").trim(),
      created_at: state.workspace?.snapshot?.current_chapter || "",
    });
    state.continuity = payload.continuity;
    state.workspace = payload.workspace;
    renderContinuity();
    renderWorkspace();
    form?.reset();
    const weightEl = $("#foreshadow-weight");
    if (weightEl) weightEl.value = "5";
    showToast("伏笔已加入连续性系统");
  } catch (error) {
    showToast(error.message, true);
  }
}

/* ---- Source ---- */
export async function extractSource(event) {
  event.preventDefault();
  const fileEl = $("#source-file");
  const file = fileEl?.files[0];
  const text = file ? await file.text() : ($("#source-content")?.value || "");
  const extractBtn = $("#source-extract");
  const statusEl = $("#source-status");
  if (extractBtn) extractBtn.disabled = true;
  if (statusEl) statusEl.textContent = "正在分块、提取并合并来源信号…";
  try {
    const payload = await extractSourceAPI(
      ($("#source-id")?.value || "").trim(),
      $("#source-focus")?.value || "style",
      text
    );
    state.workspace = payload.workspace;
    renderWorkspace();
    if (statusEl) statusEl.textContent = "来源包提取完成，可以审阅或晋升";
  } catch (error) {
    if (statusEl) statusEl.textContent = error.message;
    showToast(error.message, true);
  } finally {
    if (extractBtn) extractBtn.disabled = false;
  }
}

/* ---- Writer ---- */
export async function runWriter(event) {
  event.preventDefault();
  const submit = $("#write-submit");
  const cancel = $("#write-cancel");
  const progress = $("#write-progress");
  if (submit) submit.disabled = true;
  if (cancel) cancel.disabled = true;
  if (progress) {
    progress.classList.remove("error");
    progress.textContent = "正在组装上下文并执行写作、观察和状态结算…";
  }
  try {
    const payload = await runWriterAPI(
      $("#write-guidance")?.value || "",
      Number($("#write-words")?.value || 3000)
    );
    state.workspace = payload.workspace;
    renderWorkspace();
    $("#write-dialog")?.close();
    showToast(`${payload.result.chapter_id} 已完成，${formatNumber(payload.result.word_count)} 字`);
    if (payload.result.draft_path) {
      const match = state.workspace?.documents?.chapters?.find((item) =>
        item.path.endsWith(`/${payload.result.chapter_id}.md`)
      );
      const { openDocument } = await import("./router.js");
      if (match) await openDocument(match.path, true);
    }
  } catch (error) {
    if (progress) {
      progress.classList.add("error");
      progress.textContent = error.message;
    }
  } finally {
    if (submit) submit.disabled = false;
    if (cancel) cancel.disabled = false;
  }
}
