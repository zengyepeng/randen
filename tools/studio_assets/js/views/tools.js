/* ===== Creation Wizard (modal dialog) ===== */
import { $, $$ } from "../utils.js";

let _ewStep = 1;
let _ewResults = {};

export function initCreationWizard() {
  $("#engine-launch")?.addEventListener("click", () => {
    const dlg = $("#engine-dialog");
    if (dlg) { dlg.showModal(); goStep(1); }
  });
  $("#engine-dialog-close")?.addEventListener("click", () => $("#engine-dialog")?.close());
  $("#engine-dialog")?.addEventListener("click", (e) => { if (e.target === e.currentTarget) e.target.close(); });

  // Next/prev buttons
  $$(".ed-next").forEach(btn => {
    btn.addEventListener("click", () => { const s = parseInt(btn.dataset.next); if (s) goStep(s); });
  });
  $$(".ed-prev").forEach(btn => {
    btn.addEventListener("click", () => { const s = parseInt(btn.dataset.prev); if (s) goStep(s); });
  });
  $(".ed-done")?.addEventListener("click", () => $("#engine-dialog")?.close());

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
  <strong>${_ewEsc(m.genre)}</strong>
  <span class="ew-tags">
    <span class="ew-tag ew-tg-tr">${_ewEsc(m.traffic)}</span>
    <span class="ew-tag ew-tg-co">${_ewEsc(m.competition)}</span>
    <span class="ew-tag">新人${_ewEsc(m.newcomer)}</span>
  </span>
  <p class="ew-tip">${_ewEsc(m.tip)}</p>
</div>`).join('');
      }
      _ewResults.market = true;
      _enableNext(2);
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });

  // Step 2: Dissect
  $("#ew-dissect")?.addEventListener("click", async () => {
    const text = $("#ew-dissect-text")?.value || "";
    const btn = $("#ew-dissect"); const out = $("#ew-dissect-out");
    if (!text.trim()) { if (out) _ewErr(out, new Error("请先粘贴参考作品正文")); return; }
    if (btn) btn.disabled = true;
    if (out) { out.hidden = false; out.textContent = "拆解中…"; }
    try {
      const data = await _ewPost("/api/dissect", { text, title: $("#ew-dissect-title")?.value || "" });
      const h = (data.hooks_detected||[]).map(x => `<span class="ew-chip">${_ewEsc(x)}</span>`).join('');
      const g = (data.golden_finger_style||[]).map(x => `<span class="ew-chip">${_ewEsc(x)}</span>`).join('');
      if (out) out.innerHTML = `
<div class="ew-item">
  <p><strong>${_ewEsc(data.title)}</strong> · 约${data.estimated_words}字 · ${_ewEsc(data.rhythm)}</p>
  ${h ? `<p>🎣 钩子: ${h}</p>` : ''}
  ${g ? `<p>⚡ 金手指: ${g}</p>` : ''}
  <p class="ew-tip">${_ewEsc(data.suggestion)}</p>
</div>`;
      _ewResults.dissect = true;
      _enableNext(3);
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });

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
  <p><strong>分类：${_ewEsc(data.genre)}</strong></p>
  <p>💡 ${_ewEsc(s.premise)}</p>
  <p>🎯 金手指：${_ewEsc(s.golden_finger)}</p>
  <p>⚠️ 代价：${_ewEsc(s.golden_finger_cost)}</p>
  ${(data.next_steps||[]).map(x => `<p>→ ${_ewEsc(x)}</p>`).join('')}
</div>`;
      _ewResults.idea = true;
      _enableNext(4);
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });

  // Step 4: Opening
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
<div class="${i.passed?'ew-ok':'ew-no'}">${i.passed?'✅':'❌'} ${_ewEsc(i.check)}${!i.passed?`<br><small>${_ewEsc(i.detail)}</small>`:''}</div>`).join('');
      if (out) out.innerHTML = `
<div class="ew-item">
  <div class="ew-score" style="color:${c}">${data.score}<small>/100</small></div>
  <p class="ew-verdict">${_ewEsc(data.verdict)}</p>
  ${checks}
</div>`;
    } catch (e) { if (out) _ewErr(out, e); }
    if (btn) btn.disabled = false;
  });
}

function goStep(n) {
  _ewStep = n;
  $$(".ed-step").forEach(el => el.classList.toggle("active", parseInt(el.dataset.step) === n));
  $$(".ed-dot").forEach((el, i) => {
    el.classList.remove("active", "done");
    if (i + 1 === n) el.classList.add("active");
    else if (i + 1 < n) el.classList.add("done");
  });
  $$(".ed-line").forEach((el, i) => el.classList.toggle("done", i < n - 1));
  // Reset next button disabled state to check results
  if (_ewResults["market"]) _enableNext(2);
  if (_ewResults["dissect"]) _enableNext(3);
  if (_ewResults["idea"]) _enableNext(4);
}

function _enableNext(step) {
  const btn = document.querySelector(`.ed-next[data-next="${step}"]`);
  if (btn) btn.disabled = false;
}

function _ewErr(el, e) { el.innerHTML = `<span style="color:#ef4444">⚠ ${_ewEsc(e.message||e)}</span>`; el.hidden = false; }

function _ewEsc(s) { const m = {'<':'&lt;','>':'&gt;','&':'&amp;'}; return String(s||'').replace(/[<>&]/g, c => m[c]||c); }

async function _ewPost(url, body) {
  const res = await fetch(url, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body) });
  if (!res.ok) { const err = await res.json().catch(()=>({detail:res.statusText})); throw new Error(err.detail||`请求失败 (${res.status})`); }
  return res.json();
}
