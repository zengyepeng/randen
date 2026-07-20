/* ===== Creation Wizard (modal dialog) — v2: 独立步骤 + 文件上传 + 多书管理 ===== */
import { $, $$ } from "../utils.js";


let _ewBooks = [];

// Restore dissected books from localStorage
try {
  const saved = localStorage.getItem('randen-dissected-books');
  if (saved) _ewBooks = JSON.parse(saved);
} catch(_) { _ewBooks = []; }

function _saveBooksToStorage() {
  try { localStorage.setItem('randen-dissected-books', JSON.stringify(_ewBooks.slice(0, 20))); } catch(_) {}
}
 // 已拆书目 [{title, result, time}]

export function initCreationWizard() {
  // Auto-open wizard on first visit
  if (!localStorage.getItem('randen-wizard-visited')) {
    localStorage.setItem('randen-wizard-visited', '1');
    setTimeout(() => {
      const dlg = $("#engine-dialog");
      if (dlg && !dlg.open) { dlg.showModal(); goStep(1); }
    }, 800);
  }

  $("#engine-launch")?.addEventListener("click", () => {
    const dlg = $("#engine-dialog");
    if (dlg) { dlg.showModal(); goStep(parseInt(localStorage.getItem("randen-wizard-step")||"1")); }
  });
  $("#engine-dialog-close")?.addEventListener("click", () => $("#engine-dialog")?.close());
  $("#engine-dialog")?.addEventListener("click", (e) => { if (e.target === e.currentTarget) e.target.close(); });

  // Step dots clickable to jump
  $$(".ed-dot").forEach(dot => {
    dot.addEventListener("click", () => {
      const n = Array.from(dot.parentElement.children).filter(c => c.classList.contains("ed-dot")).indexOf(dot) + 1;
      goStep(n);
    });
    dot.style.cursor = "pointer";
  });

  // Next/prev buttons
  $$(".ed-next").forEach(btn => {
    btn.addEventListener("click", () => { const s = parseInt(btn.dataset.next); if (s) goStep(s); });
  });
  $$(".ed-prev").forEach(btn => {
    btn.addEventListener("click", () => { const s = parseInt(btn.dataset.prev); if (s) goStep(s); });
  });
  
  $(".ed-done")?.addEventListener("click", () => {
    $("#engine-dialog")?.close();
    // Switch to writing view in the studio
    try {
      import("../router.js").then(m => m.switchView("chapters", true));
    } catch(_) {}
  });
  $("#ew-start-writing")?.addEventListener("click", () => {
    $("#engine-dialog")?.close();
    try { import("../router.js").then(m => { m.switchView("chapters", true); }); } catch(_) {}
  });


  // Step 1: Market
  $("#ew-market")?.addEventListener("click", async () => {
    const btn = $("#ew-market"); const out = $("#ew-market-out");
    if (btn) btn.disabled = true;
    if (out) { out.hidden = false; out.textContent = "分析中…"; }
    try {
      const data = await _ewPost("/api/market", { platform: $("#ew-platform")?.value || "默认" });
      if (out) {
        out.innerHTML = data.markets.map(m => `
<div class="ew-item">
  <strong>${_esc(m.genre)}</strong>
  <span class="ew-tags">
    <span class="ew-tag ew-tg-tr">${_esc(m.traffic)}</span>
    <span class="ew-tag ew-tg-co">${_esc(m.competition)}</span>
    <span class="ew-tag">新人${_esc(m.newcomer)}</span>
  </span>
  <p class="ew-tip">${_esc(m.tip)}</p>
</div>`).join('');
      }
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });

  // Step 2: Dissect — 文件上传 + 多书管理
  _initFileUpload();
  _renderBookList();
  _initMergeButton();

  // Step 3: Idea
  $("#ew-idea")?.addEventListener("click", async () => {
    const premise = $("#ew-idea-premise")?.value || "";
    const btn = $("#ew-idea"); const out = $("#ew-idea-out");
    if (!premise.trim()) { if (out) _ewErr(out, new Error("请输入你的灵感")); return; }
    if (btn) btn.disabled = true;
    if (out) { out.hidden = false; out.textContent = "分析中…"; }
    try {
      const data = await _ewPost("/api/idea", { premise });
      const s = data.setting;
      if (out) out.innerHTML = `
<div class="ew-item">
  <p><strong>分类：${_esc(data.genre)}</strong></p>
  <p>💡 ${_esc(s.premise)}</p>
  <p>🎯 金手指：${_esc(s.golden_finger)}</p>
  <p>⚠️ 代价：${_esc(s.golden_finger_cost)}</p>
  ${(data.next_steps||[]).map(x => `<p>→ ${_esc(x)}</p>`).join('')}
</div>`;
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });

  // Step 4: Opening
  
  // Export full report button
  $("#ew-export-report")?.addEventListener("click", () => {
    const parts = [];
    parts.push('# 创作准备报告\n');
    parts.push(`*生成时间: ${new Date().toLocaleString()}*\n`);
    
    const market = document.querySelector('#ew-market-out')?.textContent;
    if (market && !market.includes('分析中')) parts.push('## 市场分析\n' + market);
    
    if (_ewBooks.length) {
      parts.push('## 拆书分析 (' + _ewBooks.length + '本)\n');
      _ewBooks.forEach(b => parts.push('### ' + (b.title||'未命名') + '\n```json\n' + JSON.stringify(b.result,null,2) + '\n```\n'));
    }
    
    const idea = document.querySelector('#ew-idea-out')?.textContent;
    if (idea && !idea.includes('分析中')) parts.push('## 脑洞\n' + idea);
    
    const opening = document.querySelector('#ew-opening-out')?.textContent;
    if (opening && !opening.includes('诊断中')) parts.push('## 开篇诊断\n' + opening);
    
    const blob = new Blob([parts.join('\n\n')], {type:'text/markdown'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '创作准备报告_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.md';
    a.click();
    URL.revokeObjectURL(a.href);
  });

  $("#ew-opening")?.addEventListener("click", async () => {
    const text = $("#ew-opening-text")?.value || "";
    const btn = $("#ew-opening"); const out = $("#ew-opening-out");
    if (text.length < 50) { if (out) _ewErr(out, new Error("请至少粘贴200字开篇")); return; }
    if (btn) btn.disabled = true;
    if (out) { out.hidden = false; out.textContent = "诊断中…"; }
    try {
      const data = await _ewPost("/api/opening", { text });
      const c = data.score >= 85 ? '#22c55e' : data.score >= 60 ? '#f59e0b' : '#ef4444';
      const checks = (data.items||[]).map(i => `
<div class="${i.passed?'ew-ok':'ew-no'}">${i.passed?'✅':'❌'} ${_esc(i.check)}${!i.passed?`<br><small>${_esc(i.detail)}</small>`:''}</div>`).join('');
      if (out) out.innerHTML = `
<div class="ew-item">
  <div class="ew-score" style="color:${c}">${data.score}<small>/100</small></div>
  <p class="ew-verdict">${_esc(data.verdict)}</p>
  ${checks}
</div>`;
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });
  
  // Outline generation
  $("#ew-gen-outline")?.addEventListener("click", async () => {
    const premise = $("#ew-idea-premise")?.value || "";
    if (!premise.trim()) return;
    const btn = $("#ew-gen-outline"); const out = $("#ew-outline-out");
    if (btn) btn.disabled = true;
    if (out) { out.hidden = false; out.textContent = "生成大纲中…"; }
    try {
      const data = await _ewPost("/api/generate_outline", { premise });
      if (out) {
        out.innerHTML = `
<div class="ew-item ew-outline">
  <h4>📖 ${_esc(data.title_hook)}</h4>
  <p style="font-size:.85rem;color:var(--text-secondary)">${_esc(data.tagline)}</p>
  <p style="font-size:.82rem"><strong>预估总章数: ${data.total_chapters_estimate} 章</strong></p>
  ${data.arcs.map(a => `
  <div class="ew-arc-card">
    <strong>📑 ${_esc(a.name)}</strong>
    <small>约 ${a.chapters} 章</small>
    <p style="margin:2px 0;font-size:.8rem;color:var(--text-secondary)">目标: ${_esc(a.goal)}</p>
    <p style="margin:0;font-size:.78rem;color:var(--text-tertiary)">⭐ ${_esc(a.key_event)}</p>
  </div>`).join('')}
  <p class="ew-tip" style="margin-top:8px">💡 ${_esc(data.first_chapter_hook)}</p>
  <p class="ew-tip">📝 ${_esc(data.writing_tip)}</p>
</div>`;
      }

      _addSaveButton(out, "outline", data, data.title_hook || "大纲");
      // Add apply-to-project button
      const applyBtn = document.createElement('button');
      applyBtn.className = 'ew-save-btn';
      applyBtn.textContent = '📝 写入项目大纲';
      applyBtn.style.cssText = 'margin-left:8px';
      applyBtn.addEventListener('click', async () => {
        applyBtn.disabled = true; applyBtn.textContent = '写入中...';
        try {
          await _ewPost('/api/save', { type: 'outline_full', data: data, title: data.title_hook || '大纲' });
          applyBtn.textContent = '✅ 已写入 src/outline.md';
        } catch(e) { applyBtn.textContent = '⚠ 失败'; }
      });
      out.querySelector('.ew-save-btn')?.after(applyBtn);

    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });

  // Show outline button after idea result appears
  const ideaCheck = setInterval(() => {
    const out = $("#ew-idea-out");
    const genBtn = $("#ew-gen-outline");
    if (out && !out.hidden && genBtn) { genBtn.hidden = false; clearInterval(ideaCheck); }
  }, 500);

  loadFAQIntoWizard();
}

/* ── 文件上传 ── */
function _initFileUpload() {
  const dropzone = $("#ew-dropzone");
  const fileInput = $("#ew-file-input");
  const textarea = $("#ew-dissect-text");
  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) _readFile(file, textarea, dropzone);
  });
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) _readFile(file, textarea, dropzone);
  });

  // Dissect single book (deep)
  $("#ew-dissect-new")?.addEventListener("click", async () => {
    const text = textarea?.value || "";
    const title = $("#ew-dissect-title")?.value || "";
    const out = $("#ew-dissect-out");
    if (text.length < 100) { if (out) _ewErr(out, new Error("请先粘贴或拖拽上传正文内容")); return; }
    const btn = $("#ew-dissect-new");
    if (btn) btn.disabled = true;
    if (out) { out.hidden = false; out.textContent = "正在拆解整本书…"; }
    try {
      const data = await _ewPost("/api/dissect/deep", { text, title: title || "未命名" });
      _ewBooks.push({ title: title || "未命名", result: data, time: new Date().toLocaleTimeString() });
      _saveBooksToStorage();
      if (out) _showDissectResult(out, data);
      _renderBookList();
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });
}

function _readFile(file, textarea, dropzone) {
  if (!file.name.endsWith(".txt") && !file.name.endsWith(".md")) {
    alert("仅支持 .txt 和 .md 文件");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    if (textarea) textarea.value = reader.result;
    if (dropzone) dropzone.querySelector("span").textContent = `📄 ${file.name} (${(file.size/1024).toFixed(1)} KB) 已加载`;
  };
  reader.readAsText(file, "UTF-8");
}

function _showDissectResult(out, data) {
  _addExportButtons(out, data, data.title);
  const hooks = (data.hooks_detected||[]).map(x => `<span class="ew-chip">${_esc(x)}</span>`).join('');
  const gfs = (data.golden_finger_style||[]).map(x => `<span class="ew-chip">${_esc(x)}</span>`).join('');
  let chapterHtml = "";
  if (data.chapter_details?.length) {
    chapterHtml = data.chapter_details.map(c => `
      <div class="ew-chapter-row"><strong>Ch${c.chapter}</strong> (${c.words}字) · ${(c.hooks||[]).join("、")} · ${_esc(c.key_event||"")}</div>
    `).join("");
    chapterHtml = `<details class="ew-chapters"><summary>📑 章节拆解 (${data.chapter_details.length}章)</summary>${chapterHtml}</details>`;
  }
  out.innerHTML = `
<div class="ew-item">
  <p><strong>📖 ${_esc(data.title)}</strong> · 约${data.estimated_words}字 · ${_esc(data.rhythm)}</p>
  ${hooks ? `<p>🎣 钩子: ${hooks}</p>` : ''}
  ${gfs ? `<p>⚡ 金手指: ${gfs}</p>` : ''}
  ${chapterHtml}
  <p class="ew-tip">${_esc(data.suggestion)}</p>
</div>`;
}

/* ── 已拆书目 ── */
function _renderBookList() {
  const list = $("#ew-book-list");
  if (!list) return;
  if (!_ewBooks.length) { list.innerHTML = "<small style='color:var(--text-tertiary)'>暂无已拆书目</small>"; return; }
  list.innerHTML = _ewBooks.map((b, i) => `
    <div class="ew-book-chip" data-idx="${i}">
      <span class="ew-book-check">
        <input type="checkbox" class="ew-book-select" data-idx="${i}">
      </span>
      <span class="ew-book-title">📖 ${_esc(b.title)}</span>
      <span class="ew-book-time">${b.time}</span>
      <button class="ew-book-del" data-idx="${i}" title="删除">×</button>
    </div>
  `).join('');

  // Delete buttons
  $$(".ew-book-del").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.idx);
      _ewBooks.splice(idx, 1);
      _renderBookList();
    });
  });

  // Click to review
  $$(".ew-book-chip").forEach(chip => {
    chip.addEventListener("click", (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") return;
      const idx = parseInt(chip.dataset.idx);
      if (_ewBooks[idx]) _showDissectResult($("#ew-dissect-out"), _ewBooks[idx].result);
    });
  });
}

/* ── 多书融合 ── */
function _initMergeButton() {
  $("#ew-merge")?.addEventListener("click", async () => {
    const selected = $$(".ew-book-select:checked");
    if (selected.length < 2) { alert("请至少勾选 2 本书进行融合分析"); return; }
    const results = [];
    selected.forEach(cb => { const i = parseInt(cb.dataset.idx); if (_ewBooks[i]) results.push(_ewBooks[i].result); });
    const out = $("#ew-dissect-out"); const btn = $("#ew-merge");
    if (btn) btn.disabled = true;
    if (out) { out.hidden = false; out.textContent = "融合分析中…"; }
    try {
      const data = await _ewPost("/api/dissect/merge", { results });
      if (out) out.innerHTML = `
<div class="ew-item ew-merged">
  <h4>📚 ${data.book_count} 本书融合分析</h4>
  <p>${data.books.map(b => "📖 "+_esc(b)).join("  ")}</p>
  <p>总字数: ${data.total_words}</p>
  ${data.common_hook_patterns?.length ? `<p>🎣 共性钩子: ${data.common_hook_patterns.map(_esc).join("、")}</p>` : ""}
  ${data.common_golden_fingers?.length ? `<p>⚡ 共性金手指: ${data.common_golden_fingers.map(_esc).join("、")}</p>` : ""}
  <p>🎵 主导节奏: ${_esc(data.dominant_rhythm)} (${_esc(data.rhythm_breakdown)})</p>
  <p class="ew-tip">${_esc(data.suggestion)}</p>
</div>${_diffSection(data.differences)}`;
        _addExportButtons(out, data, '融合分析');
  } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });
}

/* ── Navigation ── */
function goStep(n) {\n  localStorage.setItem("randen-wizard-step", String(n));
  $$(".ed-step").forEach(el => el.classList.toggle("active", parseInt(el.dataset.step) === n));
  $$(".ed-dot").forEach((el, i) => {
    el.classList.remove("active", "done");
    if (i + 1 === n) el.classList.add("active");
    else if (i + 1 < n) el.classList.add("done");
  });
  $$(".ed-line").forEach((el, i) => el.classList.toggle("done", i < n - 1));
}

/* ── Helpers ── */
function _ewErr(el, e) { el.innerHTML = `<span style="color:#ef4444">⚠ ${_esc(e.message||e)}</span>`; el.hidden = false; }
function _esc(s) { const m = {'<':'&lt;','>':'&gt;','&':'&amp;'}; return String(s||'').replace(/[<>&]/g, c => m[c]||c); }
async function _ewPost(url, body) {
  const res = await fetch(url, { method: "POST", headers: {"Content-Type":"application/json","X-Randen-Studio":"1"}, body: JSON.stringify(body) });
  if (!res.ok) { const err = await res.json().catch(()=>({detail:res.statusText})); throw new Error(err.error||err.detail||`请求失败 (${res.status})`); }
  return res.json();
}

/* ── Export helpers ── */
function _diffSection(diffs) {
  if (!diffs?.length) return "";
  return `<hr style="margin:12px 0;border:none;border-top:1px solid var(--border-subtle)">
<h4 style="font-size:.85rem">🔍 各书差异与定位</h4>
${diffs.map(d => `
<div style="margin-bottom:8px;padding:8px;border-radius:6px;background:var(--surface-subtle)">
  <strong>📖 ${_esc(d.title)}</strong>
  <p style="margin:2px 0;font-size:.8rem;color:var(--text-secondary)">
    ${d.unique_hooks?.length ? '独特钩子: '+d.unique_hooks.map(_esc).join('、') : ''}
    ${d.unique_golden_fingers?.length ? ' | 独特金手指: '+d.unique_golden_fingers.map(_esc).join('、') : ''}
    ${!d.unique_hooks?.length && !d.unique_golden_fingers?.length ? '与其它书高度相似' : ''}
  </p>
  <p style="margin:0;font-size:.78rem;color:var(--text-tertiary)">🎯 目标读者: ${_esc(d.target)}</p>
</div>`).join('')}`;
}

function _addExportButtons(container, resultData, label) {
  if (!container) return;
  const bar = document.createElement("div");
  bar.className = "ew-export-bar";
  const copyBtn = document.createElement("button");
  copyBtn.className = "ew-run"; copyBtn.textContent = "📋 复制";
  copyBtn.style.cssText = "font-size:.75rem;padding:4px 10px;margin:4px 4px 0 0";
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(JSON.stringify(resultData, null, 2));
    copyBtn.textContent = "✅ 已复制";
    setTimeout(() => { copyBtn.textContent = "📋 复制"; }, 1500);
  });
  bar.append(copyBtn);
  container.prepend(bar);
}


async function loadFAQIntoWizard() {
  const root = $("#ew-faq-list");
  if (!root) return;
  try {
    const data = await _ewPost("/api/faq", {});
    root.innerHTML = "";
    Object.entries(data.faq).forEach(([cat, items]) => {
      const dt = document.createElement("details");
      dt.style.cssText = "margin-bottom:6px";
      const sum = document.createElement("summary");
      sum.textContent = cat;
      sum.style.cssText = "font-weight:600;font-size:.84rem;cursor:pointer;padding:4px 0";
      dt.append(sum);
      items.forEach(i => {
        const p = document.createElement("p");
        p.style.cssText = "font-size:.8rem;color:var(--text-secondary);margin:2px 0 8px 12px;line-height:1.5";
        p.innerHTML = `<strong>Q: ${_esc(i.q)}</strong><br>A: ${_esc(i.a)}`;
        dt.append(p);
      });
      root.append(dt);
    });
  } catch (_) { root.innerHTML = "<small>加载失败</small>"; }
}

function _addSaveButton(container, resultType, data, title) {
  if (!container || container.querySelector('.ew-save-btn')) return;
  const btn = document.createElement('button');
  btn.className = 'ew-save-btn';
  btn.textContent = '💾 保存到项目';
  btn.addEventListener('click', async () => {
    btn.disabled = true; btn.textContent = '保存中...';
    try {
      const r = await _ewPost('/api/save', { type: resultType, data: data, title: title });
      btn.textContent = '✅ 已保存';
      btn.style.background = '#22c55e';
      setTimeout(() => { btn.textContent = '💾 保存到项目'; btn.style.background = ''; }, 2000);
    } catch(e) { btn.textContent = '⚠ 失败'; btn.disabled = false; }
  });
  container.prepend(btn);
}
