/* ===== Materials View ===== */
import { $, $$, showToast } from "../utils.js";

let _matState = { materials: [], stats: {}, currentCat: "", editing: false, editId: null };

export async function loadMaterials() {
  try {
    const res = await fetch("/api/materials", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
      body: JSON.stringify({ category: _matState.currentCat }),
    });
    if (!res.ok) throw new Error("加载失败");
    const data = await res.json();
    _matState.materials = data.materials || [];
    _matState.stats = data.stats || {};
    renderMaterials();
  } catch (e) { showToast("素材库加载失败: " + e.message, true); }
}

function renderMaterials() {
  renderCategories();
  renderList();
}

function renderCategories() {
  const root = $("#mat-categories");
  if (!root) return;
  const cats = _matState.stats.categories || [];
  root.innerHTML = cats.map(c => `
    <div class="mat-cat-chip ${_matState.currentCat === c.key ? 'active' : ''}" data-cat="${c.key}">
      <span>${c.icon||''} ${c.label}</span>
      <small>${c.count||0}</small>
    </div>
  `).join('') + `
    <div class="mat-cat-chip ${_matState.currentCat === '' ? 'active' : ''}" data-cat="">
      <span>📋 全部</span>
      <small>${_matState.stats.total||0}</small>
    </div>`;

  $$(".mat-cat-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      _matState.currentCat = chip.dataset.cat;
      loadMaterials();
    });
  });
}

function renderList() {
  const root = $("#mat-list");
  if (!root) return;
  const mats = _matState.materials;
  if (!mats.length) {
    root.innerHTML = '<p class="empty-state">暂无素材，点击左侧「+ 新建素材」开始</p>';
    return;
  }
  root.innerHTML = mats.map(m => `
    <article class="mat-card" data-id="${m.id}">
      <div class="mat-card-header">
        <span class="mat-cat-badge">${m.category_label}</span>
        <strong>${esc(m.title)}</strong>
        <span class="mat-usage-badge">${m.usage === 'background' ? '仅背景' : m.usage === 'writing' ? '仅写作' : '通用'}</span>
      </div>
      <p class="mat-card-preview">${esc(m.content||'').substring(0, 120)}${(m.content||'').length > 120 ? '…' : ''}</p>
      ${m.tags?.length ? `<div class="mat-tags">${m.tags.map(t => `<span class="mat-tag">${esc(t)}</span>`).join('')}</div>` : ''}
      <div class="mat-card-actions">
        <button class="text-button mat-edit-btn" data-id="${m.id}">编辑</button>
        <button class="text-button mat-del-btn" data-id="${m.id}" style="color:#ef4444">删除</button>
      </div>
    </article>
  `).join('');

  // Edit buttons
  $$(".mat-edit-btn").forEach(btn => {
    btn.addEventListener("click", () => openEditor(btn.dataset.id));
  });
  // Delete buttons
  $$(".mat-del-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!confirm("确认删除这个素材？")) return;
      await apiPost("/api/material/delete", { id: btn.dataset.id });
      loadMaterials();
    });
  });
}

function openEditor(id) {
  _matState.editing = true;
  _matState.editId = id || null;
  const editor = $("#mat-editor");
  const list = $("#mat-list");
  if (editor) editor.hidden = false;
  if (list) list.hidden = true;

  if (id) {
    const mat = _matState.materials.find(m => m.id === id);
    if (mat) {
      $("#mat-edit-title").value = mat.title || "";
      $("#mat-edit-content").value = mat.content || "";
      $("#mat-edit-cat").value = mat.category || "note";
      $("#mat-edit-usage").value = mat.usage || "both";
    }
  } else {
    $("#mat-edit-title").value = "";
    $("#mat-edit-content").value = "";
    $("#mat-edit-cat").value = "note";
    $("#mat-edit-usage").value = "both";
  }
}

$("#mat-new-btn")?.addEventListener("click", () => openEditor(null));
$("#mat-cancel")?.addEventListener("click", () => {
  _matState.editing = false;
  $("#mat-editor").hidden = true;
  $("#mat-list").hidden = false;
});
$("#mat-save")?.addEventListener("click", async () => {
  const title = $("#mat-edit-title")?.value || "";
  const content = $("#mat-edit-content")?.value || "";
  const category = $("#mat-edit-cat")?.value || "note";
  const usage = $("#mat-edit-usage")?.value || "both";
  if (!title.trim() && !content.trim()) { showToast("请填写标题或内容", true); return; }

  try {
    if (_matState.editId) {
      await apiPost("/api/material/update", { id: _matState.editId, updates: { title, content, category, usage } });
    } else {
      await apiPost("/api/material/create", { category, title, content, usage });
    }
    _matState.editing = false;
    _matState.editId = null;
    $("#mat-editor").hidden = true;
    $("#mat-list").hidden = false;
    loadMaterials();
  } catch (e) { showToast("保存失败: " + e.message, true); }
});

$("#materials-refresh")?.addEventListener("click", () => loadMaterials());

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
    body: JSON.stringify(body),
  });
  if (!res.ok) { const err = await res.json().catch(()=>({})); throw new Error(err.error||"请求失败"); }
  return res.json();
}

function esc(s) { return String(s||'').replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]||c)); }
