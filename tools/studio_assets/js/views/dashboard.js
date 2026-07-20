/* ===== Dashboard View ===== */

import { state } from "../state.js";
import { $, labels, readinessLabels, formatNumber } from "../utils.js";

export function renderWorkspace() {
  const { snapshot, model } = state.workspace;
  const bookTitle = $("#book-title");
  const bookLocation = $("#book-location");
  if (bookTitle) bookTitle.textContent = snapshot.title;
  if (bookLocation) bookLocation.textContent = `${snapshot.current_arc} / ${snapshot.current_chapter}`;

  const mWords = $("#metric-words");
  const mChapters = $("#metric-chapters");
  const mChars = $("#metric-characters");
  const mHooks = $("#metric-hooks");
  if (mWords) mWords.textContent = formatNumber(snapshot.writing_units);
  if (mChapters) mChapters.textContent = formatNumber(snapshot.chapters);
  if (mChars) mChars.textContent = formatNumber(snapshot.characters);
  if (mHooks) mHooks.textContent = formatNumber(snapshot.pending_foreshadowing);

  const percent = snapshot.target_units
    ? Math.min(100, Math.round((snapshot.writing_units / snapshot.target_units) * 100))
    : 0;
  const progressPct = $("#progress-percent");
  const progressCur = $("#progress-current");
  const progressTgt = $("#progress-target");
  const progressFill = $("#progress-fill");
  const progressTrack = $(".progress-track");

  if (progressPct) progressPct.textContent = `${percent}%`;
  if (progressCur) progressCur.textContent = `${formatNumber(snapshot.writing_units)} 字`;
  if (progressTgt) progressTgt.textContent = snapshot.target_units
    ? `目标 ${formatNumber(snapshot.target_units)} 字`
    : "目标未设置";
  if (progressFill) progressFill.style.width = `${percent}%`;
  if (progressTrack) progressTrack.setAttribute("aria-valuenow", String(percent));

  const modelState = $("#model-state");
  const writeOpen = $("#write-open");
  const modelNameInput = $("#model-name");

  if (modelState) {
    modelState.textContent = model.configured ? model.name : "模型未配置";
    modelState.classList.toggle("ready", model.configured);
  }
  if (model.configured && modelNameInput && !modelNameInput.value) modelNameInput.value = model.name;
  if (writeOpen) {
    writeOpen.disabled = !model.configured;
    writeOpen.title = model.configured ? "" : "请通过环境变量配置 LLM_API_KEY";
  }

  renderReadiness(snapshot.readiness);
  renderRecentChapters();
  renderNextActions(snapshot.next_actions);
  fillFocus(snapshot.creative_focus);

  const factArc = $("#fact-arc");
  const factChapter = $("#fact-chapter");
  const factStage = $("#fact-stage");
  const factWorld = $("#fact-world");
  const factTokens = $("#fact-tokens");
  const factReviewScore = $("#fact-review-score");

  if (factArc) factArc.textContent = snapshot.current_arc;
  if (factChapter) factChapter.textContent = snapshot.current_chapter;
  if (factStage) factStage.textContent = snapshot.stage;
  if (factWorld) factWorld.textContent = String(snapshot.world_documents);
  if (factTokens) factTokens.textContent = formatNumber(snapshot.total_tokens);
  if (factReviewScore) {
    factReviewScore.textContent = snapshot.reviewed_chapters
      ? `${snapshot.average_review_score} / 100`
      : "-";
  }

  renderDocumentList(state.view === "dashboard" ? "chapters" : state.view);
  renderOperations();
}

function renderReadiness(readiness) {
  const root = $("#readiness-list");
  if (!root) return;
  root.replaceChildren();
  let readyCount = 0;
  Object.entries(readinessLabels).forEach(([key, label]) => {
    const ready = Boolean(readiness[key]);
    if (ready) readyCount += 1;
    const row = document.createElement("div");
    row.className = `readiness-row${ready ? " ready" : ""}`;
    const name = document.createElement("span");
    name.textContent = label;
    const status = document.createElement("span");
    status.className = "readiness-state";
    status.textContent = ready ? "就绪" : "待完善";
    row.append(name, status);
    root.append(row);
  });
  const score = $("#readiness-score");
  if (score) score.textContent = `${readyCount} / ${Object.keys(readinessLabels).length}`;
}

function renderRecentChapters() {
  const root = $("#recent-chapters");
  if (!root) return;
  root.replaceChildren();
  const chapters = (state.workspace?.documents?.chapters || []).slice(-5).reverse();
  if (!chapters.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "尚无正文";
    root.append(empty);
    return;
  }
  chapters.forEach((doc) => {
    const button = document.createElement("button");
    button.className = "recent-row";
    button.type = "button";
    const title = document.createElement("span");
    title.textContent = doc.title;
    const meta = document.createElement("span");
    meta.textContent = doc.subtitle;
    button.append(title, meta);
    button.addEventListener("click", async () => {
      const { openDocument } = await import("../router.js");
      openDocument(doc.path, true);
    });
    root.append(button);
  });
}

function renderNextActions(actions) {
  const root = $("#next-actions");
  if (!root) return;
  root.replaceChildren();
  actions.forEach((action) => {
    const span = document.createElement("span");
    span.className = "next-action";
    span.textContent = action;
    root.append(span);
  });
}

export function fillFocus(focus) {
  const goalEl = $("#focus-goal");
  const keepEl = $("#focus-keep");
  const avoidEl = $("#focus-avoid");
  const notesEl = $("#focus-notes");
  if (goalEl) goalEl.value = focus.goal || "";
  if (keepEl) keepEl.value = (focus.must_keep || []).join("\n");
  if (avoidEl) avoidEl.value = (focus.must_avoid || []).join("\n");
  if (notesEl) notesEl.value = (focus.notes || []).join("\n");
}

export function renderDocumentList(group) {
  const root = $("#document-list");
  const groupTitle = $("#document-group-title");
  const docCount = $("#document-count");
  if (!root) return;
  root.replaceChildren();
  const documents = state.workspace?.documents?.[group] || [];
  if (groupTitle) groupTitle.textContent = labels[group] || "最近章节";
  if (docCount) docCount.textContent = String(documents.length);
  if (!documents.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = group === "chapters" ? "尚无正文" : "暂无文档";
    root.append(empty);
    return;
  }
  documents.forEach((doc) => {
    const button = document.createElement("button");
    button.className = "document-item";
    button.classList.toggle("active", state.document?.path === doc.path);
    button.type = "button";
    button.setAttribute("role", "listitem");
    const title = document.createElement("strong");
    title.textContent = doc.title;
    const subtitle = document.createElement("span");
    subtitle.textContent = doc.subtitle;
    button.append(title, subtitle);
    button.addEventListener("click", async () => {
      const { openDocument } = await import("../router.js");
      openDocument(doc.path, true);
    });
    root.append(button);
  });
}

export function renderOperations() {
  const operations = state.workspace?.operations || {};
  const diagnostics = operations.diagnostics || [];
  const diagnosticRoot = $("#diagnostic-list");
  if (diagnosticRoot) {
    diagnosticRoot.replaceChildren();
    diagnostics.forEach((item) => {
      const row = document.createElement("div");
      row.className = `operation-row${item.ok ? " ok" : ""}`;
      const name = document.createElement("strong");
      name.textContent = item.name;
      const detail = document.createElement("span");
      detail.textContent = item.detail;
      row.append(name, detail);
      diagnosticRoot.append(row);
    });
  }
  const sync = operations.sync || {};
  const syncStatus = $("#sync-status");
  if (syncStatus) {
    syncStatus.textContent = sync.needs_sync
      ? `待同步：大纲 ${sync.outline_pending ? "有变更" : "已同步"}，角色卡 ${sync.cards || 0}/${sync.profiles || 0}`
      : "src 与 data 已同步";
  }
  renderSourcePacks(operations.source_packs || []);
}

function renderSourcePacks(packs) {
  const root = $("#source-list");
  const countEl = $("#source-count");
  if (!root) return;
  root.replaceChildren();
  if (countEl) countEl.textContent = String(packs.length);
  if (!packs.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "尚无来源包";
    root.append(empty);
    return;
  }
  packs.forEach((pack) => {
    const row = document.createElement("article");
    row.className = "source-row";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = pack.source_id;
    const meta = document.createElement("span");
    meta.textContent = [pack.style_ready ? "风格" : "", pack.setting_ready ? "设定" : ""]
      .filter(Boolean).join(" + ") || "提取中";
    copy.append(title, meta);
    const actions = document.createElement("div");
    actions.className = "row-actions";
    [["审阅", "review"], ["全部晋升", "promote"], ["合成风格", "synthesize"]].forEach(([label, action]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "text-button";
      button.textContent = label;
      button.addEventListener("click", async () => {
        const { runSourceActionAPI } = await import("../api.js");
        const { showToast } = await import("../utils.js");
        const statusEl = $("#source-status");
        if (statusEl) statusEl.textContent = "正在执行来源操作…";
        try {
          const payload = await runSourceActionAPI(action, pack.source_id);
          state.workspace = payload.workspace;
          renderWorkspace();
          const reportEl = $("#source-report");
          if (action === "review" && reportEl) reportEl.textContent = payload.result.review_report || "无报告";
          if (statusEl) {
            statusEl.textContent = action === "promote" ? "已晋升到当前作品" : action === "synthesize" ? "合成风格已刷新" : "来源报告已生成";
          }
        } catch (error) {
          if (statusEl) statusEl.textContent = error.message;
          showToast(error.message, true);
        }
      });
      actions.append(button);
    });
    row.append(copy, actions);
    root.append(row);
  });
}

  const guide = $("#onboarding-guide");
  if (!guide) return;

  // Count ready items
  let readyCount = 0;
  Object.values(readiness).forEach(v => { if (v) readyCount++; });

  // Hide if >75% ready or dismissed
  const dismissed = localStorage.getItem("randen-onboarding-dismissed");
  if (dismissed || readyCount >= 4) {
    guide.hidden = true;
    return;
  }

  guide.hidden = false;

  // Mark steps as checked
  const stepMap = {
    foundation: "onboard-step-outline",
    characters: "onboard-step-char",
    ai_configured: "onboard-step-ai",
    outline: "onboard-step-outline",
  };
  Object.entries(readiness).forEach(([key, val]) => {
    const stepId = stepMap[key];
    if (val && stepId) {
      const el = document.getElementById(stepId);
      if (el) el.classList.add("checked");
    }
  });

  // Dismiss button
  $("#onboarding-dismiss")?.addEventListener("click", () => {
    guide.hidden = true;
    localStorage.setItem("randen-onboarding-dismissed", "1");
  });
}
