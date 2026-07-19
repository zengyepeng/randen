/* ===== AI Agents View ===== */

import { state } from "../state.js";
import { $, $$ } from "../utils.js";

export function chooseAgent(agent) {
  state.agent = agent;
  $$('[data-agent]').forEach((button) => button.classList.toggle("active", button.dataset.agent === agent));
  const submitBtn = $("#chat-submit");
  const inputEl = $("#chat-input");
  if (submitBtn) submitBtn.textContent = `发送给 ${agent === "goethe" ? "Goethe" : "Dante"}`;
  if (inputEl) {
    inputEl.placeholder = agent === "goethe"
      ? "例如：检查现有资产，帮我把第一篇推进到可写状态。"
      : "例如：写下一章，控制在 3000 字，保持当前创作罗盘。";
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
