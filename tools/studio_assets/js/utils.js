/* ===== Utility Functions ===== */

export const $ = (selector) => document.querySelector(selector);
export const $$ = (selector) => Array.from(document.querySelectorAll(selector));

export const labels = {
  story: "故事资产",
  characters: "人物档案",
  world: "世界设定",
  chapters: "正文章节",
};

export const readinessLabels = {
  author_intent: "作者意图",
  background: "故事背景",
  foundation: "基础设定",
  characters: "主要人物",
  outline: "可写大纲",
  creative_focus: "创作罗盘",
};

export function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(Number(value || 0));
}

export function countWritingUnits(text) {
  const withoutHeadings = text.replace(/^\s{0,3}#{1,6}\s+.*$/gm, "");
  const cjk = withoutHeadings.match(/[\u3400-\u4dbf\u4e00-\u9fff]/g) || [];
  const words = withoutHeadings
    .replace(/[\u3400-\u4dbf\u4e00-\u9fff]/g, " ")
    .match(/[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*/g) || [];
  return cjk.length + words.length;
}

let toastTimer = null;
export function showToast(message, error = false) {
  const toast = $("#toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

export function setSaveState(message, dirty = false) {
  const el = $("#save-state");
  const btn = $("#save-document");
  if (el) el.textContent = message;
  if (btn) btn.disabled = !dirty;
}
