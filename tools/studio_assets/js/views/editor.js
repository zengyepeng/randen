/* ===== Editor View ===== */

import { $, formatNumber, countWritingUnits } from "../utils.js";

export function updateEditorCount() {
  const editor = $("#document-editor");
  const wordCount = $("#editor-word-count");
  if (!editor || !wordCount) return;
  const count = countWritingUnits(editor.value);
  wordCount.textContent = `${formatNumber(count)} 字`;
}
