/* ===== Emotion Dashboard View ===== */

import { $ } from "../utils.js";

// ---- Mock Data ----
const emotionArcData = [
  { chapter: "Ch.1 开端", position: 10, value: 3, type: "" },
  { chapter: "Ch.2 展开", position: 20, value: 4, type: "" },
  { chapter: "Ch.3 相遇", position: 30, value: 7, type: "peak" },
  { chapter: "Ch.4 暗涌", position: 40, value: 4, type: "" },
  { chapter: "Ch.5 转折", position: 50, value: 2, type: "valley" },
  { chapter: "Ch.6 重构", position: 60, value: 6, type: "" },
  { chapter: "Ch.7 高潮", position: 70, value: 9, type: "peak" },
  { chapter: "Ch.8 收束", position: 85, value: 7, type: "turning" },
];

const retentionData = [
  {
    zone: "开头（约 500 字）",
    level: "green",
    label: "低风险",
    advice: "钩子有力，开篇节奏紧凑。继续保持悬念推进，前 3 段内完成核心设定暗示。",
  },
  {
    zone: "中段（第 3–6 章）",
    level: "yellow",
    label: "注意",
    advice: "情感张力出现波动。建议在第 4 章结尾增加反转钩子，提升翻页驱动。",
  },
  {
    zone: "结尾悬念",
    level: "red",
    label: "高风险",
    advice: "当前章节结尾未设置明确悬念。读者好奇心指数下降 18%。建议最后 300 字埋一个未曾揭露的伏笔。",
  },
];

const chekhovGuns = [
  { name: "祖父遗留的怀表", chapter: "Ch.1", status: "pending" },
  { name: "窗台枯萎的栀子花", chapter: "Ch.3", status: "pending" },
  { name: "地下室上锁的铁箱", chapter: "Ch.2", status: "planned" },
  { name: "警官的异常沉默", chapter: "Ch.5", status: "pending" },
];

const voiceHealth = [
  { name: "主角·林砚秋", score: 92, level: "distinct" },
  { name: "导师·沈青岚", score: 78, level: "moderate" },
  { name: "对手·顾泽", score: 85, level: "distinct" },
  { name: "助手·小唐", score: 55, level: "similar" },
  { name: "路人·报社主编", score: 45, level: "similar" },
];

// ---- Render Functions ----

export function renderEmotionDashboard() {
  renderArcChart();
  renderRetention();
  renderChekhovGuns();
  renderVoiceHealth();
}

function renderArcChart() {
  const container = $("#emotion-arc-chart");
  if (!container) return;

  const maxVal = 10;
  const points = emotionArcData.map((d) => {
    const x = d.position;
    const y = 100 - (d.value / maxVal) * 80;
    return { ...d, x, y };
  });

  const pathD = points
    .map((p, i) => {
      const prev = i > 0 ? points[i - 1] : p;
      const cpx = (prev.x + p.x) / 2;
      return i === 0
        ? `M ${p.x} ${p.y}`
        : `Q ${prev.x} ${p.y} ${cpx} ${(prev.y + p.y) / 2} T ${p.x} ${p.y}`;
    })
    .join(" ");

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 100 100");
  svg.setAttribute("preserveAspectRatio", "none");
  svg.classList.add("arc-svg");

  // Shadow fill
  const shadowPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
  shadowPath.setAttribute("d", `${pathD} L ${points[points.length - 1].x} 100 L ${points[0].x} 100 Z`);
  shadowPath.setAttribute("fill", "var(--accent-soft, #f5e8c5)");
  shadowPath.setAttribute("opacity", "0.3");
  svg.appendChild(shadowPath);

  // Line
  const linePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
  linePath.setAttribute("d", pathD);
  linePath.setAttribute("fill", "none");
  linePath.setAttribute("stroke", "var(--accent, #a87813)");
  linePath.setAttribute("stroke-width", "1.8");
  linePath.setAttribute("stroke-linecap", "round");
  svg.appendChild(linePath);

  container.innerHTML = "";
  container.appendChild(svg);

  // Annotation dots
  points
    .filter((p) => p.type)
    .forEach((p) => {
      const dot = document.createElement("div");
      dot.className = `arc-point ${p.type}`;
      dot.style.left = `${p.x}%`;
      dot.style.top = `${p.y}%`;
      dot.title = `${p.chapter} · 情感值 ${p.value}`;
      const label = document.createElement("span");
      label.className = "arc-label";
      label.textContent = p.chapter;
      dot.appendChild(label);
      container.appendChild(dot);
    });
}

function renderRetention() {
  const container = $("#emotion-retention");
  if (!container) return;

  container.innerHTML = retentionData
    .map(
      (item) => `
    <article class="risk-card ${item.level}">
      <h3>${item.zone}</h3>
      <span class="risk-level">${item.label}</span>
      <p>${item.advice}</p>
    </article>`
    )
    .join("");
}

function renderChekhovGuns() {
  const container = $("#emotion-guns");
  if (!container) return;

  container.innerHTML = chekhovGuns
    .map(
      (gun) => `
    <div class="gun-item">
      <span class="gun-name">${gun.name}</span>
      <span class="gun-chapter">引入: ${gun.chapter}</span>
      <span class="gun-status ${gun.status}">${gun.status === "pending" ? "未回收" : "计划中"}</span>
    </div>`
    )
    .join("");
}

function renderVoiceHealth() {
  const container = $("#emotion-voice");
  if (!container) return;

  container.innerHTML = voiceHealth
    .map(
      (v) => `
    <div class="voice-bar-row">
      <span class="voice-name" title="${v.name}">${v.name}</span>
      <div class="voice-bar-track">
        <div class="voice-bar-fill ${v.level}" style="width: ${v.score}%"></div>
      </div>
      <span class="voice-score">${v.score}%</span>
    </div>`
    )
    .join("");
}
