/* ===== Tools View + Creation Engine ===== */

import { $, $$ } from "../utils.js";

/* ===== Creation Engine ===== */
let _faqData = null;

export function initCreationEngine() {
  const bind = (id, handler) => $(`#engine-${id}`)?.addEventListener("click", handler);

  bind("market", async () => {
    const btn = $("#engine-market"); const result = $("#engine-market-result");
    if (btn) btn.disabled = true;
    if (result) { result.hidden = false; result.textContent = "\u23f3 分析中\u2026"; }
    try {
      const data = await _apiPost("/api/market", { platform: $("#engine-platform")?.value || "默认" });
      if (result) {
        result.innerHTML = data.markets.map(m => `
<div class="engine-result-item">
  <div class="eri-header">
    <strong>${_esc(m.genre)}</strong>
    <span class="eri-tags">
      <span class="eri-tag eri-tag--traffic">流量:${_esc(m.traffic)}</span>
      <span class="eri-tag eri-tag--comp">竞争:${_esc(m.competition)}</span>
      <span class="eri-tag">新人${_esc(m.newcomer)}</span>
    </span>
  </div>
  <p class="eri-tip">\ud83d\udca1 ${_esc(m.tip)}</p>
</div>`).join('');
        _highlightFlow(1);
      }
    } catch (e) { if (result) _showError(result, e); }
    if (btn) btn.disabled = false;
  });

  bind("dissect", async () => {
    const text = $("#engine-dissect-text")?.value || "";
    const btn = $("#engine-dissect"); const result = $("#engine-dissect-result");
    if (!text.trim()) { if (result) _showError(result, new Error("请先粘贴正文内容")); return; }
    if (btn) btn.disabled = true;
    if (result) { result.hidden = false; result.textContent = "\u23f3 拆解中\u2026"; }
    try {
      const data = await _apiPost("/api/dissect", { text, title: $("#engine-dissect-title")?.value || "未命名" });
      if (result) {
        const hooks = (data.hooks_detected || []).map(h => `<span class="eri-chip">${_esc(h)}</span>`).join(' ');
        const gfs = (data.golden_finger_style || []).map(g => `<span class="eri-chip">${_esc(g)}</span>`).join(' ');
        result.innerHTML = `
<div class="engine-result-item">
  <div class="eri-header"><strong>\ud83d\udcd6 ${_esc(data.title)}</strong></div>
  <div class="eri-stat-row">
    <span class="eri-stat">\ud83d\udcdd 约${data.estimated_words}字</span>
    <span class="eri-stat">\ud83d\udcd1 约${data.estimated_chapters}章</span>
    <span class="eri-stat">\ud83c\udfb5 ${_esc(data.rhythm)}</span>
  </div>
  <div class="eri-section"><strong>\ud83c\udfa3 钩子模式</strong><p>${hooks || '未检测到明显钩子'}</p></div>
  <div class="eri-section"><strong>\u26a1 金手指类型</strong><p>${gfs || '未检测到明显金手指'}</p></div>
  <div class="eri-section eri-suggestion">${_esc(data.suggestion)}</div>
</div>`;
        _highlightFlow(2);
      }
    } catch (e) { if (result) _showError(result, e); }
    if (btn) btn.disabled = false;
  });

  bind("idea", async () => {
    const premise = $("#engine-idea-premise")?.value || "";
    const btn = $("#engine-idea"); const result = $("#engine-idea-result");
    if (!premise.trim()) { if (result) _showError(result, new Error("请先输入灵感")); return; }
    if (btn) btn.disabled = true;
    if (result) { result.hidden = false; result.textContent = "\u23f3 分析中\u2026"; }
    try {
      const data = await _apiPost("/api/idea", { premise });
      const s = data.setting;
      if (result) {
        const qs = (data.prompt_questions || []).map(q => `<p>\u2022 ${_esc(q)}</p>`).join('');
        const ns = (data.next_steps || []).map(s => `\ud83d\ude80 ${_esc(s)}<br>`).join('');
        result.innerHTML = `
<div class="engine-result-item">
  <div class="eri-header"><strong>\ud83c\udff7 ${_esc(data.genre)}</strong></div>
  <div class="eri-kv"><span>\u7075\u611f</span><span>${_esc(s.premise)}</span></div>
  <div class="eri-kv"><span>\u91d1\u624b\u6307</span><span>${_esc(s.golden_finger)}</span></div>
  <div class="eri-kv"><span>\u4ee3\u4ef7\u9650\u5236</span><span>${_esc(s.golden_finger_cost)}</span></div>
  <div class="eri-kv"><span>\u76ee\u6807\u60c5\u7eea</span><span>${_esc(s.target_emotion)}</span></div>
  <div class="eri-kv"><span>\u4e3b\u89d2\u7f3a\u9677</span><span>${_esc(s.protagonist_flaw)}</span></div>
  <div class="eri-section"><strong>\u2753 \u8fd8\u9700\u60f3\u6e05\u695a</strong>${qs}</div>
  <div class="eri-section eri-suggestion">${ns}</div>
</div>`;
        _highlightFlow(3);
      }
    } catch (e) { if (result) _showError(result, e); }
    if (btn) btn.disabled = false;
  });

  bind("opening", async () => {
    const text = $("#engine-opening-text")?.value || "";
    const btn = $("#engine-opening"); const result = $("#engine-opening-result");
    if (text.length < 50) { if (result) _showError(result, new Error("请至少粘贴200字开篇")); return; }
    if (btn) btn.disabled = true;
    if (result) { result.hidden = false; result.textContent = "\u23f3 诊断中\u2026"; }
    try {
      const data = await _apiPost("/api/opening", { text });
      const pct = data.score;
      const color = pct >= 85 ? '#22c55e' : pct >= 60 ? '#f59e0b' : '#ef4444';
      const checks = (data.items || []).map(i => `
    <div class="eri-check ${i.passed ? 'eri-check-pass' : 'eri-check-fail'}">
      <span>${i.passed ? '\u2705' : '\u274c'}</span>
      <span>${_esc(i.check)}</span>
      ${!i.passed ? `<small>${_esc(i.detail)}</small>` : ''}
    </div>`).join('');
      if (result) {
        result.innerHTML = `
<div class="engine-result-item">
  <div class="eri-score" style="--score-color:${color};--score-pct:${pct}%">
    <span class="eri-score-num">${pct}</span><span class="eri-score-label">/ 100</span>
  </div>
  <p class="eri-verdict">${_esc(data.verdict)}</p>
  ${checks}
  ${data.quick_fix ? `<div class="eri-section eri-suggestion">\u26a1 ${_esc(data.quick_fix)}</div>` : ''}
</div>`;
        _highlightFlow(4);
      }
    } catch (e) { if (result) _showError(result, e); }
    if (btn) btn.disabled = false;
  });

  loadFAQ();
}

async function loadFAQ() {
  if (_faqData) { _renderFAQ(_faqData); return; }
  const root = $("#engine-faq");
  if (!root) return;
  try { _faqData = await _apiPost("/api/faq", {}); _renderFAQ(_faqData); }
  catch (_) { if (root) root.innerHTML = '<small class="eri-error">加载FAQ失败</small>'; }
}

function _renderFAQ(data) {
  const root = $("#engine-faq");
  if (!root) return;
  root.replaceChildren();
  let activeChip = null;
  Object.entries(data.faq).forEach(([cat, items]) => {
    const catLabel = document.createElement("div");
    catLabel.className = "faq-category"; catLabel.textContent = cat;
    root.append(catLabel);
    items.forEach(item => {
      const chip = document.createElement("span");
      chip.className = "faq-chip"; chip.textContent = item.q;
      chip.addEventListener("click", () => {
        if (activeChip === chip) {
          chip.classList.remove("active");
          const panel = chip.nextElementSibling;
          if (panel?.classList.contains("faq-answer-panel")) { panel.remove(); activeChip = null; return; }
        }
        if (activeChip) { activeChip.classList.remove("active"); const prev = activeChip.nextElementSibling; if (prev?.classList.contains("faq-answer-panel")) prev.remove(); }
        chip.classList.add("active"); activeChip = chip;
        const panel = document.createElement("div");
        panel.className = "faq-answer-panel"; panel.textContent = "\ud83d\udcac " + item.a;
        chip.after(panel);
      });
      root.append(chip);
    });
  });
}

function _highlightFlow(step) {
  $$(".flow-step").forEach((el, i) => el.classList.toggle("active", i + 1 === step));
}

function _showError(el, err) {
  el.innerHTML = `<span class="eri-error">\u26a0 ${_esc(err.message || err)}</span>`;
  el.hidden = false;
}

function _esc(s) {
  const map = { '<': '&lt;', '>': '&gt;', '&': '&amp;' };
  return String(s || '').replace(/[<>&]/g, c => map[c] || c);
}

async function _apiPost(url, body) {
  const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || "请求失败 (" + res.status + ")"); }
  return res.json();
}
