/* ===== Editor View ===== */

import { $, formatNumber, countWritingUnits, setSaveState } from "../utils.js";

let _autoSaveTimer = null;
let _draftPath = null;

export function updateEditorCount() {
  const editor = $("#document-editor");
  const wordCount = $("#editor-word-count");
  if (!editor || !wordCount) return;
  const count = countWritingUnits(editor.value);
  wordCount.textContent = `${formatNumber(count)} 字`;
  // Warn if over 5000
  wordCount.style.color = count > 5000 ? "#f59e0b" : "";
}

/* ── Autosave ── */
export function initEditorAutosave() {
  const editor = $("#document-editor");
  if (!editor) return;

  // Auto-save every 30 seconds
  editor.addEventListener("input", () => {
    updateEditorCount();
    _scheduleDraftSave(editor);
  });

  // Save on blur
  editor.addEventListener("blur", () => _saveDraft(editor));

  // Check for unsaved draft on load
  _checkDraftRecovery(editor);
}

/* ── Write Pipeline ── */
export function initWritePipeline() {
  $("#write-chapter-btn")?.addEventListener("click", () => {
    $("#write-inline").hidden = !$("#write-inline").hidden;
  });

  $("#write-inline-cancel")?.addEventListener("click", () => {
    $("#write-inline").hidden = true;
    $("#write-inline-status").textContent = "";
  });

  $("#write-inline-start")?.addEventListener("click", async () => {
    const words = parseInt($("#write-inline-words")?.value || "3000");
    const guidance = $("#write-inline-guidance")?.value || "";
    const status = $("#write-inline-status");
    const btn = $("#write-inline-start");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ 写作中…"; }
    if (status) status.textContent = "正在组装上下文 + AI 写作 + 审查…";

    try {
      const res = await fetch("/api/write", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({ target_words: words, guidance }),
      });
      const data = await res.json();
      if (data.result?.content || data.result) {
        const chapter = typeof data.result === "string" ? data.result : (data.result.content || JSON.stringify(data.result, null, 2));
        const editor = $("#document-editor");
        if (editor) editor.value = chapter;
        updateEditorCount();
        $("#editor-path").textContent = "新章节 (AI 生成)";
        if (status) status.textContent = "✅ 写作完成！点击保存按钮保存到项目。";
        // Refresh workspace
        try {
          const { loadWorkspace } = await import("../api.js");
          const { state } = await import("../state.js");
          state.workspace = await loadWorkspace();
          const { renderWorkspace } = await import("../views/dashboard.js");
          renderWorkspace();
        } catch(_) {}
        $("#write-inline").hidden = true;
      } else if (data.error) {
        if (status) status.textContent = "❌ " + data.error;
      }
    } catch(e) {
      if (status) status.textContent = "❌ 请求失败: " + (e.message||e);
    }
    if (btn) { btn.disabled = false; btn.textContent = "开始写作"; }
  });
}

/* ── Chapter Reader ── */
export function initChapterReader() {
  let _readerChapterIdx = -1;
  let _readerChapters = [];

  $("#reader-mode-btn")?.addEventListener("click", async () => {
    const { state } = await import("../state.js");
    const { getDocumentAPI } = await import("../api.js");
    const chapters = state.workspace?.documents?.chapters || [];
    _readerChapters = chapters;

    if (!chapters.length) {
      alert("暂无章节可阅读");
      return;
    }

    // Find current chapter index
    _readerChapterIdx = chapters.findIndex(c => c.path === state.document?.path);
    if (_readerChapterIdx < 0) _readerChapterIdx = chapters.length - 1;

    $("#document-editor").hidden = true;
    $("#chapter-reader").hidden = false;
    $("#write-chapter-btn").hidden = true;
    $("#reader-mode-btn").textContent = "✏️ 编辑";
    $("#save-document").hidden = true;

    await _loadReaderChapter(chapters[_readerChapterIdx]);
  });

  // Toggle back to edit mode
  $("#reader-mode-btn")?.addEventListener("click", () => {
    if (!$("#chapter-reader").hidden) {
      // Exit reader
      $("#chapter-reader").hidden = true;
      $("#document-editor").hidden = false;
      $("#write-chapter-btn").hidden = false;
      $("#reader-mode-btn").textContent = "📖 阅读";
      $("#save-document").hidden = false;
    }
  });

  $("#reader-prev")?.addEventListener("click", () => {
    if (_readerChapterIdx > 0) {
      _readerChapterIdx--;
      _loadReaderChapter(_readerChapters[_readerChapterIdx]);
    }
  });

  $("#reader-next")?.addEventListener("click", async () => {
    if (_readerChapterIdx < _readerChapters.length - 1) {
      _readerChapterIdx++;
      await _loadReaderChapter(_readerChapters[_readerChapterIdx]);
    } else {
      alert("已经是最后一章了");
    }
  });

  $("#reader-exit")?.addEventListener("click", () => {
    $("#chapter-reader").hidden = true;
    $("#document-editor").hidden = false;
    $("#write-chapter-btn").hidden = false;
    $("#reader-mode-btn").textContent = "📖 阅读";
    $("#save-document").hidden = false;
  });

  async function _loadReaderChapter(chapter) {
    if (!chapter) return;
    const { getDocumentAPI } = await import("../api.js");
    try {
      const doc = await getDocumentAPI(chapter.path);
      $("#reader-chapter-label").textContent = `${chapter.path} — ${doc.title || ""}`;
      $("#chapter-reader-content").innerHTML = _simpleMarkdown(doc.content || "");
      $("#chapter-reader-content").scrollTop = 0;
    } catch(e) {
      $("#chapter-reader-content").innerHTML = `<p style="color:#ef4444">加载失败: ${e.message}</p>`;
    }
  }
}

function _simpleMarkdown(text) {
  let html = String(text||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  html = html.replace(/^### (.+)$/gm,'<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm,'<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm,'<h1>$1</h1>');
  html = html.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g,'<em>$1</em>');
  html = html.replace(/\n\n/g,'</p><p>');
  html = html.replace(/\n/g,'<br>');
  return `<p>${html}</p>`;
}

/* ── Token Display ── */
export function initTokenDisplay() {
  const loadTokenInfo = async () => {
    try {
      const { state } = await import("../state.js");
      const ws = state.workspace;
      const tokenEl = $("#token-info");
      if (!tokenEl) return;
      const tokens = ws?.model?.total_tokens || ws?.tokens_used || 0;
      if (tokens > 0) {
        tokenEl.hidden = false;
        tokenEl.textContent = `💰 ${(tokens/1000).toFixed(1)}K`;
      }
    } catch(_) {}
  };
  // Run once and on workspace refresh
  setTimeout(loadTokenInfo, 1000);
  // Observe workspace changes
  const observer = new MutationObserver(loadTokenInfo);
  const dash = $("#dashboard-view");
  if (dash) observer.observe(dash, { childList: true, subtree: true });
}

function _scheduleDraftSave(editor) {
  if (_autoSaveTimer) clearTimeout(_autoSaveTimer);
  _autoSaveTimer = setTimeout(() => _saveDraft(editor), 30000);
}

function _saveDraft(editor) {
  if (!_draftPath) return;
  const val = editor.value;
  if (!val.trim()) return;
  try {
    localStorage.setItem(`randen-draft-${_draftPath}`, val);
    // Brief status feedback
    setSaveState("已自动保存", false);
    setTimeout(() => {
      const s = $("#save-document");
      if (s && s.textContent === "已自动保存") setSaveState("已保存", false);
    }, 3000);
  } catch (_) {}
}

function _checkDraftRecovery(editor) {
  // This is called on load; actual recovery triggers when a document is opened
  const docObserver = new MutationObserver(() => {
    const pathEl = $("#editor-path");
    if (pathEl && pathEl.textContent) {
      _draftPath = pathEl.textContent;
      try {
        const draft = localStorage.getItem(`randen-draft-${_draftPath}`);
        if (draft && draft !== editor.value && draft.trim()) {
          if (confirm(`发现 ${_draftPath} 的未保存草稿，是否恢复？`)) {
            editor.value = draft;
            updateEditorCount();
          }
          localStorage.removeItem(`randen-draft-${_draftPath}`);
        }
      } catch (_) {}
    }
  });
  const pathEl = $("#editor-path");
  if (pathEl) docObserver.observe(pathEl, { characterData: true, subtree: true });
}
