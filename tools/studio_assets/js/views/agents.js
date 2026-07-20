/* ===== AI Agents View — 灵感对话 + Goethe + Dante ===== */

import { state } from "../state.js";
import { $, $$ } from "../utils.js";

let _conversationRounds = 0;
let _inspireContext = "";

export function chooseAgent(agent) {
  state.agent = agent;
  $$('[data-agent]').forEach((button) => button.classList.toggle("active", button.dataset.agent === agent));
  const submitBtn = $("#chat-submit");
  const inputEl = $("#chat-input");
  const protoBtn = $("#chat-prototype");
  const log = $("#chat-log");

  if (agent === "inspire") {
    _conversationRounds = 0;
    _inspireContext = "";
    if (submitBtn) submitBtn.textContent = "发送灵感";
    if (inputEl) inputEl.placeholder = "例如：我想写一个关于时间循环的小说，主角每天醒来都回到同一天，但每次循环都会少一个他在乎的人…";
    if (protoBtn) protoBtn.hidden = true;
    if (log) log.innerHTML = '<article class="chat-message assistant"><strong>燃灯</strong><p>💡 <strong>灵感对话模式</strong>：说出你的创作想法，我会追问、澄清、完善，最后生成一份作品雏形（故事背景 + 角色框架 + 世界观 + 第一章钩子）。现在，请告诉我你的灵感。</p></article>';
  } else if (agent === "goethe") {
    if (submitBtn) submitBtn.textContent = "发送给 Goethe";
    if (inputEl) { inputEl.placeholder = "例如：检查现有资产，帮我把第一篇推进到可写状态。"; }
    if (protoBtn) protoBtn.hidden = true;
  } else {
    if (submitBtn) submitBtn.textContent = "发送给 Dante";
    if (inputEl) { inputEl.placeholder = "例如：写下一章，控制在 3000 字，保持当前创作罗盘。"; }
    if (protoBtn) protoBtn.hidden = true;
  }
}

export function appendChatMessage(role, author, content) {
  const log = $("#chat-log");
  if (!log) return;
  const item = document.createElement("article");
  item.className = `chat-message ${role}`;
  const name = document.createElement("strong");
  name.textContent = author;
  const body = document.createElement("p");
  body.textContent = content;
  item.append(name, body);
  log.append(item);
  item.scrollIntoView({ block: "end", behavior: "smooth" });
}

export async function handleChatSubmit(event) {
  event.preventDefault();
  const input = $("#chat-input");
  const status = $("#chat-status");
  const protoBtn = $("#chat-prototype");
  const message = input?.value?.trim();
  if (!message || !input) return;

  const agent = state.agent || "inspire";
  appendChatMessage("user", "你", message);
  input.value = "";
  if (status) status.textContent = "思考中…";

  if (agent === "inspire") {
    _conversationRounds++;
    _inspireContext += `\n用户: ${message}`;

    try {
      let systemPrompt;
      if (_conversationRounds === 1) {
        systemPrompt = `你是燃灯·青灯，一位小说创作顾问。用户刚刚分享了创作灵感。请：
1. 用2-3句话表示理解(展现你真的懂了)
2. 问3个最关键的问题(帮助用户深入思考)
3. 给出一个初步的判断(这个想法适合什么类型/大概多少字数)
保持亲切、专业、鼓励的语气。总回复控制在200字内。`;
      } else if (_conversationRounds <= 3) {
        systemPrompt = `你是燃灯·青灯。用户已经进行了${_conversationRounds}轮对话。请：
1. 基于之前的对话，追问一个更具体的问题
2. 给出一个具体的建议(角色/世界观/桥段)
3. 如果已经收集够信息，提示用户可以点击"生成作品雏形"按钮
总回复控制在150字内。`;
      } else {
        systemPrompt = `你是燃灯·青灯。用户已经进行了${_conversationRounds}轮对话，信息足够。请回复：
"信息已经很充分了！点击下方的「✨生成作品雏形」按钮，我会为你生成一份完整的作品雏形。"`;
      }

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({ agent, message, system_override: systemPrompt, context: _inspireContext }),
      });
      const data = await res.json();
      if (data.reply) {
        appendChatMessage("assistant", "燃灯", data.reply);
        _inspireContext += `\n燃灯: ${data.reply}`;
      }
      if (_conversationRounds >= 2 && protoBtn) protoBtn.hidden = false;
    } catch (e) {
      appendChatMessage("assistant", "燃灯", "抱歉，连接失败。请检查模型配置后重试。");
    }
  } else {
    // Goethe/Dante - existing logic
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({ agent, message }),
      });
      const data = await res.json();
      if (data.reply) appendChatMessage("assistant", agent === "goethe" ? "Goethe" : "Dante", data.reply);
    } catch (e) {
      appendChatMessage("assistant", "燃灯", "抱歉，连接失败。请检查模型配置后重试。");
    }
  }

  if (status) status.textContent = "";
}

export function initPrototypeButton() {
  $("#chat-prototype")?.addEventListener("click", async () => {
    const btn = $("#chat-prototype");
    const status = $("#chat-status");
    if (btn) btn.disabled = true;
    if (status) status.textContent = "正在生成作品雏形…";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
        body: JSON.stringify({
          agent: "inspire",
          message: `请基于我们${_conversationRounds}轮对话的内容，生成一份完整的「作品雏形」文档。格式如下：

## 📖 故事背景
（150字内概括核心冲突和世界观）

## 👤 核心角色
（2-3个主要角色，每个50字: 姓名/身份/目标/缺陷）

## 🌍 世界观亮点
（3条最独特的设定，每条30字）

## 📑 篇章结构
（3篇大纲: 篇名/章数/核心目标/关键事件）

## ✍️ 第一章钩子
（具体的第一章开篇钩子设计，80字，让读者翻页）

## 🎯 独特卖点
（一句话说明这本书和同类作品的区别）

以下是对话历史：${_inspireContext}`,
          system_override: "你是燃灯·青灯，一位专业的网文编辑和创作顾问。请基于对话历史，生成一份完整的作品雏形文档。严格按照格式输出，语言简洁有力。",
        }),
      });
      const data = await res.json();
      if (data.reply) {
        appendChatMessage("assistant", "燃灯·作品雏形", data.reply);
        // Auto-save to project
        try {
          await fetch("/api/save", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Randen-Studio": "1" },
            body: JSON.stringify({ type: "prototype", data: { text: data.reply }, title: "灵感对话作品雏形" }),
          });
          appendChatMessage("assistant", "燃灯", "✅ 雏形已自动保存到项目的 data/wizard_outputs/ 目录");
        } catch (_) {}
      }
    } catch (e) {
      appendChatMessage("assistant", "燃灯", "抱歉，生成失败。请检查 API 配置后重试。");
    }
    if (btn) btn.disabled = false;
    if (status) status.textContent = "";
  });
}
