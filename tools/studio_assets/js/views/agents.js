/* ===== AI Agents View — 灵感对话 v4 + Goethe + Dante =====
 * v4: 多会话管理 · 人格选择器 · 导出对话 · 跨功能串联 · 图片灵感
 *    + v3: Markdown · 快捷追问 · 持久化 · 消息操作 · Enter发送 · 动画
 */

import { state } from "../state.js";
import { $, $$ } from "../utils.js";

/* ── State ── */
const STORAGE_PREFIX = "randen-inspire";
let _activeConvId = null;   // currently active conversation id
let _conversations = [];    // [{id, title, messages, rounds, context, persona, createdAt}]
let _conversationRounds = 0;
let _inspireContext = "";
let _activePersona = "warm"; // warm | sharp | analyst | creative | worldbuilder

/* ── Persona definitions ── */
const PERSONAS = {
  warm:    { emoji: "🔥", name: "温暖协作",  desc: "鼓励式沟通，陪你一起打磨想法",   flavor: "亲切、鼓励、温暖的语气。像朋友一样聊天。" },
  sharp:   { emoji: "⚡", name: "毒舌编辑",  desc: "直接犀利，直击要害不给面子",      flavor: "犀利、毒舌、不留情面。直接指出问题，但出发点是帮你写出好作品。像严苛的编辑。" },
  analyst: { emoji: "🔬", name: "硬核分析",  desc: "数据驱动，拆解套路和可行情",      flavor: "理性、分析性、数据驱动的语气。从市场、结构、读者心理学角度分析。" },
  creative:{ emoji: "🎨", name: "创意激荡",  desc: "发散思维，不断抛出新鲜视角",      flavor: "跳跃、发散、天马行空的语气。不断抛出意想不到的角度和创意。" },
  world:   { emoji: "🌍", name: "世界架构师",desc: "专注世界观，深挖设定和规则",      flavor: "严谨、系统性的语气。专注于世界观的一致性、细节和深度。" },
};

/* ═══ Conversation persistence ═══ */
function _saveAll() {
  if (!_activeConvId) return;
  _syncActiveConv();
  try { localStorage.setItem(`${STORAGE_PREFIX}-convs`, JSON.stringify(_conversations)); } catch (_) {}
  try { localStorage.setItem(`${STORAGE_PREFIX}-active`, _activeConvId); } catch (_) {}
}

function _syncActiveConv() {
  const idx = _conversations.findIndex(c => c.id === _activeConvId);
  if (idx < 0) return;
  const log = $("#chat-log");
  const messages = [];
  if (log) {
    log.querySelectorAll(".chat-message").forEach(msg => {
      const role = msg.classList.contains("user") ? "user" : msg.classList.contains("assistant") ? "assistant" : null;
      if (!role) return;
      messages.push({ role, html: msg.innerHTML });
    });
  }
  _conversations[idx].messages = messages;
  _conversations[idx].rounds = _conversationRounds;
  _conversations[idx].context = _inspireContext;
  _conversations[idx].persona = _activePersona;
  _conversations[idx].updatedAt = Date.now();
}

function _loadConversation(convId) {
  const conv = _conversations.find(c => c.id === convId);
  if (!conv) return false;
  const log = $("#chat-log");
  if (!log) return false;

  _activeConvId = convId;
  _conversationRounds = conv.rounds || 0;
  _inspireContext = conv.context || "";
  _activePersona = conv.persona || "warm";

  log.innerHTML = "";
  (conv.messages || []).forEach(m => {
    const article = document.createElement("article");
    article.className = `chat-message ${m.role}`;
    article.innerHTML = m.html;
    log.append(article);
    _bindMessageActions(article);
  });

  _updatePersonaUI();
  const protoBtn = $("#chat-prototype");
  if (protoBtn) protoBtn.hidden = _conversationRounds < 2;
  _scrollToBottom(false);
  _showQuickRepliesForLastAssistant();
  return true;
}

/* ── Conversation list sidebar ── */
function _renderConvList() {
  const list = $("#conv-list");
  if (!list) return;
  _conversations.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));

  list.innerHTML = _conversations.map(c => {
    const active = c.id === _activeConvId ? " active" : "";
    const persona = PERSONAS[c.persona] || PERSONAS.warm;
    const title = c.title || "未命名对话";
    const time = c.updatedAt ? new Date(c.updatedAt).toLocaleString("zh-CN", {month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}) : "";
    return `<div class="conv-item${active}" data-conv-id="${c.id}">
      <span class="conv-icon">${persona.emoji}</span>
      <span class="conv-info">
        <span class="conv-title">${_esc(title)}</span>
        <span class="conv-meta">${c.rounds||0}轮 · ${time}</span>
      </span>
      <button class="conv-del" data-conv-id="${c.id}" title="删除">×</button>
    </div>`;
  }).join("") || '<div class="conv-empty">暂无对话记录</div>';

  // Bind click: switch conversation
  list.querySelectorAll(".conv-item").forEach(item => {
    item.addEventListener("click", (e) => {
      if (e.target.classList.contains("conv-del")) return;
      const id = item.dataset.convId;
      if (id !== _activeConvId) {
        _syncActiveConv();
        _loadConversation(id);
        _saveAll();
        _renderConvList();
      }
    });
  });

  // Bind delete
  list.querySelectorAll(".conv-del").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.dataset.convId;
      if (confirm("确定删除这段对话吗？")) {
        _conversations = _conversations.filter(c => c.id !== id);
        if (id === _activeConvId) {
          _activeConvId = null;
          _newConversation();
        }
        _saveAll();
        _renderConvList();
      }
    });
  });
}

function _newConversation() {
  _syncActiveConv();
  const id = "conv_" + Date.now();
  _conversations.push({
    id, title: "新对话",
    messages: [{
      role: "assistant",
      html: '<strong>燃灯</strong><p>💡 <strong>灵感对话模式</strong>：说出你的创作想法，我会追问、澄清、完善，最后生成一份作品雏形（故事背景 + 角色框架 + 世界观 + 第一章钩子）。现在，请告诉我你的灵感。</p>'
    }],
    rounds: 0, context: "", persona: _activePersona,
    createdAt: Date.now(), updatedAt: Date.now(),
  });
  _loadConversation(id);
  _saveAll();
  _renderConvList();
}

/* ── Auto-title from first user message ── */
async function _autoTitle(userMessage) {
  if (!_activeConvId) return;
  const conv = _conversations.find(c => c.id === _activeConvId);
  if (!conv || (conv.title && conv.title !== "新对话")) return;
  // Generate title client-side: first 15 chars + "..."
  const t = userMessage.replace(/我想写|一个|关于|的故事|的小说/g, "").trim();
  conv.title = t.length > 16 ? t.substring(0, 16) + "…" : t;
  _saveAll();
  _renderConvList();
}

/* ═══ Markdown → HTML ═══ */
function _mdToHtml(text) {
  let html = String(text || "");
  html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre class="md-code"><code>$2</code></pre>');
  html = html.replace(/`([^`]+)`/g, '<code class="md-inline">$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^[*-] (.+)$/gm, '<li class="md-li">$1</li>');
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="md-li">$1</li>');
  html = html.replace(/((?:<li class="md-li">[^<]*<\/li>\n?)+)/g, '<ul class="md-ul">$1</ul>');
  const paragraphs = html.split(/\n\n+/);
  html = paragraphs.map(p => {
    if (p.startsWith('<h2') || p.startsWith('<h3') || p.startsWith('<pre') || p.startsWith('<ul')) return p;
    return `<p class="md-p">${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');
  return html;
}

/* ═══ Quick replies ═══ */
function _getQuickReplies(round) {
  if (round === 1) return [
    "这个金手指有什么代价或限制？",
    "主角是什么样的人？有什么性格缺陷？",
    "这个世界的核心矛盾是什么？",
  ];
  if (round === 2) return [
    "帮我想一个让人眼前一亮的第一章开头",
    "这个设定下，反派应该是什么样的人？",
    "有什么类似的好书可以参考？",
  ];
  if (round === 3) return [
    "我觉得信息够了，生成作品雏形吧",
    "再帮我完善一下世界观",
    "帮我设计一个核心配角",
  ];
  return [
    "感觉差不多了，来生成雏形！",
    "还有什么我没考虑到的？",
    "换一个角度重新思考这个故事",
  ];
}

function _renderQuickReplies(replies) {
  const container = $("#chat-quick-replies");
  if (!container) return;
  if (!replies?.length) { container.innerHTML = ""; return; }
  container.innerHTML = replies.map(r =>
    `<button class="quiet-button qr-chip" data-reply="${_escAttr(r)}">💬 ${_esc(r)}</button>`
  ).join('');
  container.querySelectorAll(".qr-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const text = chip.dataset.reply;
      const input = $("#chat-input");
      if (input && text) { input.value = text; input.focus(); $("#chat-form")?.dispatchEvent(new Event("submit", {cancelable:true})); }
    });
  });
  container.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function _showQuickRepliesForLastAssistant() {
  setTimeout(() => {
    const msgs = document.querySelectorAll("#chat-log .chat-message.assistant");
    if (msgs.length > 0 && _conversationRounds > 0) _renderQuickReplies(_getQuickReplies(_conversationRounds));
  }, 100);
}

/* ═══ Message actions ═══ */
function _bindMessageActions(article) {
  if (article.querySelector(".msg-actions") || article.classList.contains("user")) return;
  const actions = document.createElement("div");
  actions.className = "msg-actions";
  actions.innerHTML = `
    <button class="msg-action-btn" data-action="copy" title="复制">📋</button>
    <button class="msg-action-btn" data-action="regenerate" title="重新生成">🔄</button>
  `;
  article.append(actions);
  actions.querySelector('[data-action="copy"]').addEventListener("click", (e) => {
    e.stopPropagation();
    const text = article.textContent;
    navigator.clipboard.writeText(text).then(() => {
      const btn = actions.querySelector('[data-action="copy"]'); btn.textContent = "✅";
      setTimeout(() => { btn.textContent = "📋"; }, 1500);
    });
  });
  actions.querySelector('[data-action="regenerate"]').addEventListener("click", async (e) => {
    e.stopPropagation();
    article.remove();
    _conversationRounds = Math.max(1, _conversationRounds - 1);
    _saveAll();
    const userMsgs = document.querySelectorAll("#chat-log .chat-message.user");
    const lastUserMsg = userMsgs[userMsgs.length - 1];
    if (lastUserMsg) {
      const lastText = lastUserMsg.querySelector("p")?.textContent || "";
      if (lastText) {
        const input = $("#chat-input");
        if (input) { input.value = lastText; $("#chat-form")?.dispatchEvent(new Event("submit", {cancelable:true})); }
      }
    }
  });
}

/* ═══ Scroll management ═══ */
function _scrollToBottom(smooth = true) {
  const log = $("#chat-log");
  if (!log) return;
  log.scrollTo({ top: log.scrollHeight, behavior: smooth ? "smooth" : "instant" });
  _updateScrollButton();
}
function _updateScrollButton() {
  const log = $("#chat-log"); const btn = $("#chat-scroll-bottom");
  if (!log || !btn) return;
  btn.hidden = (log.scrollHeight - log.scrollTop - log.clientHeight) < 100;
}
function _autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
}

/* ═══ Append chat message ═══ */
export function appendChatMessage(role, author, content, isMarkdown = false) {
  const log = $("#chat-log");
  if (!log) return;
  const item = document.createElement("article");
  item.className = `chat-message ${role}`;
  item.style.opacity = "0"; item.style.transform = "translateY(8px)";
  item.style.transition = "opacity .3s ease, transform .3s ease";
  const name = document.createElement("strong");
  name.textContent = author;
  if (isMarkdown) {
    const body = document.createElement("div");
    body.className = "md-body";
    body.innerHTML = _mdToHtml(content);
    item.append(name, body);
  } else {
    const body = document.createElement("p"); body.textContent = content;
    item.append(name, body);
  }
  log.append(item);
  _bindMessageActions(item);
  _saveAll();
  requestAnimationFrame(() => { item.style.opacity = "1"; item.style.transform = "translateY(0)"; });
  _scrollToBottom(true);
}

/* ═══ Agent switching ═══ */
export function chooseAgent(agent) {
  state.agent = agent;
  $$('[data-agent]').forEach(b => b.classList.toggle("active", b.dataset.agent === agent));
  const submitBtn = $("#chat-submit");
  const inputEl = $("#chat-input");
  const protoBtn = $("#chat-prototype");
  const quickReplies = $("#chat-quick-replies");
  const quickStart = document.querySelector(".inspire-quickstart");
  const clearBtn = $("#chat-clear");
  const personaSelector = $("#persona-selector");
  const convSidebar = $("#conv-sidebar");
  const imageUpload = $("#image-inspire-area");
  const exportBtn = $("#chat-export");
  const applyBtn = $("#chat-apply");

  if (agent === "inspire") {
    // Show inspire-specific UI
    if (convSidebar) convSidebar.style.display = "";
    if (personaSelector) personaSelector.style.display = "";
    if (imageUpload) imageUpload.style.display = "";
    if (exportBtn) exportBtn.style.display = "";
    if (quickStart) quickStart.style.display = "";
    if (clearBtn) clearBtn.style.display = "";

    if (submitBtn) submitBtn.textContent = "发送灵感";
    if (inputEl) { inputEl.placeholder = "说出你的创作想法…"; inputEl.rows = 4; }

    // Load conversations from storage
    try {
      const saved = localStorage.getItem(`${STORAGE_PREFIX}-convs`);
      if (saved) _conversations = JSON.parse(saved);
    } catch (_) { _conversations = []; }
    try {
      _activeConvId = localStorage.getItem(`${STORAGE_PREFIX}-active`);
    } catch (_) { _activeConvId = null; }

    if (!_activeConvId || !_loadConversation(_activeConvId)) {
      if (_conversations.length > 0) {
        _loadConversation(_conversations[0].id);
      } else {
        _newConversation();
      }
    }
    _renderConvList();
    _updatePersonaUI();
    _checkApplyButtonVisibility();

  } else {
    // Hide inspire-specific UI, show minimal chat
    if (convSidebar) convSidebar.style.display = "none";
    if (personaSelector) personaSelector.style.display = "none";
    if (imageUpload) imageUpload.style.display = "none";
    if (exportBtn) exportBtn.style.display = "none";
    if (applyBtn) applyBtn.style.display = "none";
    if (quickStart) quickStart.style.display = "none";
    if (clearBtn) clearBtn.style.display = "none";
    if (quickReplies) quickReplies.innerHTML = "";

    if (submitBtn) submitBtn.textContent = agent === "goethe" ? "发送给 Goethe" : "发送给 Dante";
    if (inputEl) { inputEl.placeholder = agent === "goethe" ? "例如：检查现有资产…" : "例如：写下一章…"; inputEl.rows = 4; }
    if (protoBtn) protoBtn.hidden = true;
  }
  _scrollToBottom(false);
}

/* ═══ Persona selector ═══ */
function _updatePersonaUI() {
  const selector = $("#persona-select");
  if (selector) selector.value = _activePersona;
  const badge = $("#persona-badge");
  const p = PERSONAS[_activePersona];
  if (badge) badge.innerHTML = `${p.emoji} ${p.name}`;
}

export function initPersonaSelector() {
  $("#persona-select")?.addEventListener("change", (e) => {
    _activePersona = e.target.value;
    _updatePersonaUI();
    _saveAll();
  });
  _updatePersonaUI();
}

function _getPersonaFlavor() {
  return (PERSONAS[_activePersona] || PERSONAS.warm).flavor;
}

/* ═══ Image inspiration ═══ */
export function initImageInspire() {
  const dropzone = $("#image-dropzone");
  const fileInput = $("#image-file-input");
  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("dragover"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", e => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) _processImage(file, dropzone);
  });
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) _processImage(file, dropzone);
  });
}

async function _processImage(file, dropzone) {
  if (!file.type.startsWith("image/")) { alert("请上传图片文件"); return; }
  if (file.size > 5 * 1024 * 1024) { alert("图片不能超过 5MB"); return; }

  const reader = new FileReader();
  reader.onload = async () => {
    if (dropzone) dropzone.querySelector("span").textContent = "🔍 AI 正在理解图片…";
    try {
      const res = await fetch("/api/inspire/vision", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({ image: reader.result, persona: _activePersona }),
      });
      const data = await res.json();
      if (data.description) {
        appendChatMessage("assistant", "燃灯·视觉", `🖼️ ${data.description}\n\n${data.question || "这个画面给你什么灵感？"}`, true);
        _conversationRounds++;
        _inspireContext += `\n燃灯(视觉): ${data.description}`;
        _saveAll();
        _showQuickRepliesForLastAssistant();
      }
    } catch (e) {
      appendChatMessage("assistant", "燃灯", "抱歉，图片分析失败。");
    }
    if (dropzone) dropzone.querySelector("span").textContent = "🖼️ 拖拽或点击上传场景/角色参考图";
  };
  reader.readAsDataURL(file);
}

/* ═══ Export dialogue ═══ */
export function initExportButton() {
  $("#chat-export")?.addEventListener("click", () => {
    const conv = _conversations.find(c => c.id === _activeConvId);
    if (!conv) return;
    const persona = PERSONAS[conv.persona || "warm"];
    const parts = [`# 灵感对话记录\n`,
      `- **人格**: ${persona.emoji} ${persona.name}`,
      `- **轮次**: ${conv.rounds || 0} 轮`,
      `- **时间**: ${new Date(conv.createdAt).toLocaleString("zh-CN")}`,
      `\n---\n`];
    (conv.messages || []).forEach(m => {
      const tmp = document.createElement("div"); tmp.innerHTML = m.html;
      const author = tmp.querySelector("strong")?.textContent || (m.role === "user" ? "你" : "燃灯");
      const text = tmp.textContent || "";
      parts.push(`**${author}**: ${text.trim()}\n`);
    });
    const blob = new Blob([parts.join("\n")], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `灵感对话_${(conv.title||"未命名").replace(/[\\/:*?"<>|]/g,"")}_${new Date().toISOString().slice(0,10)}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
  });
}

/* ═══ Cross-feature bridge: parse prototype → apply to project ═══ */
function _checkApplyButtonVisibility() {
  const applyBtn = $("#chat-apply");
  if (!applyBtn) return;
  const msgs = document.querySelectorAll("#chat-log .chat-message.assistant");
  let hasPrototype = false;
  msgs.forEach(m => {
    const strong = m.querySelector("strong");
    if (strong && strong.textContent.includes("作品雏形")) hasPrototype = true;
  });
  applyBtn.style.display = hasPrototype ? "" : "none";
}

export function initApplyToProject() {
  $("#chat-apply")?.addEventListener("click", async () => {
    const btn = $("#chat-apply");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ 解析中…"; }

    // Find last prototype message
    const msgs = document.querySelectorAll("#chat-log .chat-message.assistant");
    let protoText = "";
    msgs.forEach(m => {
      const strong = m.querySelector("strong");
      if (strong && strong.textContent.includes("作品雏形")) {
        protoText = m.textContent || "";
      }
    });

    try {
      const res = await fetch("/api/inspire/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({ prototype: protoText }),
      });
      const data = await res.json();
      if (data.ok) {
        let summary = "✅ 雏形已应用到项目：\n";
        if (data.created_characters) summary += `👤 ${data.created_characters} 个角色\n`;
        if (data.created_world) summary += `🌍 ${data.created_world} 条世界观\n`;
        if (data.created_outline) summary += `📑 大纲已更新\n`;
        if (data.created_materials) summary += `📝 ${data.created_materials} 条素材\n`;
        appendChatMessage("assistant", "燃灯", summary);
        if (btn) { btn.textContent = "✅ 已应用"; btn.style.background = "#22c55e"; }
        // Refresh workspace
        try { const { loadWorkspace } = await import("../api.js"); state.workspace = await loadWorkspace(); (await import("../views/dashboard.js")).renderWorkspace(); } catch (_) {}
      }
    } catch (e) {
      appendChatMessage("assistant", "燃灯", `❌ 应用到项目失败: ${e.message || "请求失败"}`);
      if (btn) { btn.textContent = "🔧 应用到项目"; btn.disabled = false; }
    }
  });
}

/* ═══ Chat submit handler ═══ */
export async function handleChatSubmit(event) {
  event.preventDefault();
  const input = $("#chat-input");
  const status = $("#chat-status");
  const protoBtn = $("#chat-prototype");
  const submitBtn = $("#chat-submit");
  const message = input?.value?.trim();
  if (!message || !input) return;

  const agent = state.agent || "inspire";
  appendChatMessage("user", "你", message);
  input.value = "";
  _autoResize(input);
  _renderQuickReplies([]);

  if (status) status.textContent = "思考中…";
  const typing = $("#chat-typing"); if (typing) typing.hidden = false;
  if (submitBtn) submitBtn.disabled = true;

  if (agent === "inspire") {
    _conversationRounds++;
    _inspireContext += `\n用户: ${message}`;
    _autoTitle(message);
    const persona = _getPersonaFlavor();

    try {
      let systemPrompt;
      if (_conversationRounds === 1) {
        systemPrompt = `你是燃灯·青灯，一位小说创作顾问。${persona}\n用户刚刚分享了创作灵感。请：\n1. 用2-3句话表示理解\n2. 问3个最关键的问题\n3. 给出初步判断（适合什么类型/大概多少字数）\n总回复控制在200字内。`;
      } else if (_conversationRounds <= 3) {
        systemPrompt = `你是燃灯·青灯。${persona}\n用户已进行${_conversationRounds}轮对话。请：\n1. 追问一个更具体的问题\n2. 给一个具体建议\n3. 如果信息够，提示点击"生成作品雏形"\n总回复控制在150字内。`;
      } else {
        systemPrompt = `你是燃灯·青灯。${persona}\n用户已进行${_conversationRounds}轮对话，信息足够了。请回复："信息已经很充分了！点击下方的「✨生成作品雏形」按钮吧。"`;
      }

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({ agent, message, system_override: systemPrompt, context: _inspireContext }),
      });
      const data = await res.json();
      if (data.reply) {
        appendChatMessage("assistant", "燃灯", data.reply, true);
        _inspireContext += `\n燃灯: ${data.reply}`;
        _showQuickRepliesForLastAssistant();
      }
      if (_conversationRounds >= 2 && protoBtn) protoBtn.hidden = false;
      _checkApplyButtonVisibility();
    } catch (e) {
      appendChatMessage("assistant", "燃灯", "抱歉，连接失败。请检查模型配置后重试。");
    }
  } else {
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({ agent, message }),
      });
      const data = await res.json();
      if (data.reply) appendChatMessage("assistant", agent === "goethe" ? "Goethe" : "Dante", data.reply, true);
    } catch (e) {
      appendChatMessage("assistant", "燃灯", "抱歉，连接失败。");
    }
  }

  if (status) status.textContent = "";
  if (typing) typing.hidden = true;
  if (submitBtn) submitBtn.disabled = false;
}

/* ═══ Keyboard ═══ */
export function initChatKeyboard() {
  const input = $("#chat-input");
  if (!input) return;
  input.addEventListener("input", () => _autoResize(input));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#chat-form")?.dispatchEvent(new Event("submit", {cancelable:true})); }
  });
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "l" && state.agent === "inspire") { e.preventDefault(); _newConversation(); }
  });
}

/* ═══ Init ═══ */
export function initQuickStartChips() {
  $$(".qs-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.dataset.prompt;
      if (prompt) { const input = $("#chat-input"); if (input) { input.value = prompt; _autoResize(input); input.focus(); } }
    });
  });
}

export function initClearButton() {
  $("#chat-clear")?.addEventListener("click", () => {
    if (confirm("开始一段新的灵感对话？（当前对话会保存）")) _newConversation();
  });
}

export function initScrollButton() {
  const log = $("#chat-log"); const btn = $("#chat-scroll-bottom");
  if (!log || !btn) return;
  log.addEventListener("scroll", () => _updateScrollButton());
  btn.addEventListener("click", () => _scrollToBottom(true));
}

export function initNewConvButton() {
  $("#conv-new")?.addEventListener("click", () => _newConversation());
}

/* ═══ Prototype generation ═══ */
export function initPrototypeButton() {
  $("#chat-prototype")?.addEventListener("click", async () => {
    const btn = $("#chat-prototype");
    const status = $("#chat-status");
    const typing = $("#chat-typing");
    if (btn) btn.disabled = true;
    if (status) status.textContent = "正在生成作品雏形…";
    if (typing) typing.hidden = false;

    const persona = _getPersonaFlavor();
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({
          agent: "inspire",
          message: `请基于我们${_conversationRounds}轮对话的内容，生成一份完整的「作品雏形」文档。\n\n## 📖 故事背景\n## 👤 核心角色\n## 🌍 世界观亮点\n## 📑 篇章结构\n## ✍️ 第一章钩子\n## 🎯 独特卖点\n\n对话历史：${_inspireContext}`,
          system_override: `你是燃灯·青灯，一位专业的网文编辑和创作顾问。${persona}请基于对话历史生成完整的作品雏形文档。严格按照格式输出，每个角色和设定都要具体可写。`,
        }),
      });
      const data = await res.json();
      if (data.reply) {
        appendChatMessage("assistant", "燃灯·作品雏形", data.reply, true);
        _checkApplyButtonVisibility();
        // Auto-save
        try {
          await fetch("/api/save", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
            body: JSON.stringify({ type: "prototype", data: { text: data.reply }, title: "灵感对话作品雏形" }),
          });
        } catch (_) {}
      }
    } catch (e) {
      appendChatMessage("assistant", "燃灯", "抱歉，生成失败。请检查 API 配置后重试。");
    }
    if (btn) btn.disabled = false;
    if (typing) typing.hidden = true;
    if (status) status.textContent = "";
  });
}

/* ── Utils ── */
function _esc(s) {
  const m = {'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'};
  return String(s||'').replace(/[<>&"]/g, c => m[c]||c);
}
function _escAttr(s) { return String(s||'').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
