/* ===== Review Action Handlers ===== */

import { state } from "./state.js";
import { $, showToast } from "./utils.js";
import { runReviewAPI } from "./api.js";
import { renderWorkspace } from "./views/dashboard.js";

export async function runReview() {
  if (!state.document || state.dirty) {
    showToast(state.dirty ? "请先保存章节再审稿" : "未选择章节", true);
    return;
  }
  const dialog = $("#review-dialog");
  const loading = $("#review-loading");
  if (loading) {
    loading.hidden = false;
    loading.classList.remove("error");
    loading.textContent = "正在执行规则检查与深度审稿…";
  }
  const resultEl = $("#review-result");
  if (resultEl) resultEl.hidden = true;
  if (dialog) dialog.showModal();
  try {
    const payload = await runReviewAPI(state.document.path);
    state.workspace = payload.workspace;
    renderWorkspace();
    renderReviewResult(payload.result);
  } catch (error) {
    if (loading) {
      loading.textContent = error.message;
      loading.classList.add("error");
    }
  }
}

export function renderReviewResult(result) {
  const loading = $("#review-loading");
  const resultEl = $("#review-result");
  if (loading) loading.hidden = true;
  if (resultEl) resultEl.hidden = false;

  const scoreEl = $("#review-score");
  const verdict = $("#review-verdict");
  const summary = $("#review-summary");
  const issuesRoot = $("#review-issues");

  if (scoreEl) scoreEl.textContent = String(Math.round(Number(result.score || 0)));
  if (verdict) {
    verdict.textContent = result.passed ? "通过" : "需要修订";
    verdict.classList.toggle("ready", Boolean(result.passed));
  }
  if (summary) summary.textContent = result.summary || `${result.issues || 0} 个问题`;

  if (issuesRoot) {
    issuesRoot.replaceChildren();
    const issues = result.issue_details || [];
    if (!issues.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "未发现需要处理的问题";
      issuesRoot.append(empty);
      return;
    }
    issues.forEach((issue) => {
      const item = document.createElement("article");
      item.className = "review-issue";
      const heading = document.createElement("div");
      heading.className = "review-issue-heading";
      const category = document.createElement("strong");
      category.textContent = issue.category || "未分类";
      const severity = document.createElement("span");
      const severityName = ["critical", "warning", "info"].includes(issue.severity)
        ? issue.severity : "warning";
      severity.className = `severity ${severityName}`;
      severity.textContent = { critical: "严重", warning: "警告", info: "提示" }[severityName];
      heading.append(category, severity);
      const description = document.createElement("p");
      description.textContent = issue.description || "";
      item.append(heading, description);
      if (issue.suggestion) {
        const suggestion = document.createElement("p");
        suggestion.className = "review-suggestion";
        suggestion.textContent = `建议：${issue.suggestion}`;
        item.append(suggestion);
      }
      issuesRoot.append(item);
    });
  }
}
