/* ===== Continuity View ===== */

import { state } from "../state.js";
import { $ } from "../utils.js";

export function renderContinuity() {
  const data = state.continuity || {};
  const truth = data.truth || {};

  const truthCur = $("#truth-current");
  const truthLedger = $("#truth-ledger");
  const truthRel = $("#truth-relationships");
  if (truthCur) truthCur.textContent = truth.current_state || "尚无状态";
  if (truthLedger) truthLedger.textContent = truth.ledger || "尚无账本";
  if (truthRel) truthRel.textContent = truth.relationships || "尚无关系记录";

  const nodes = data.foreshadowing?.nodes || [];
  const hookCount = $("#foreshadow-count");
  const hookRoot = $("#foreshadow-list");
  if (hookCount) hookCount.textContent = String(nodes.length);
  if (hookRoot) {
    hookRoot.replaceChildren();
    nodes.forEach((node) => {
      const row = document.createElement("div");
      row.className = "operation-row stacked";
      const heading = document.createElement("strong");
      heading.textContent = `${node.id} · 权重 ${node.weight}`;
      const content = document.createElement("span");
      content.textContent = node.content;
      row.append(heading, content);
      hookRoot.append(row);
    });
    if (!nodes.length) hookRoot.textContent = "暂无待处理伏笔";
  }

  const workflows = data.workflows || [];
  const wfCount = $("#workflow-count");
  const wfRoot = $("#workflow-list");
  if (wfCount) wfCount.textContent = String(workflows.length);
  if (wfRoot) {
    wfRoot.replaceChildren();
    workflows.forEach((workflow) => {
      const row = document.createElement("div");
      row.className = `operation-row stacked${workflow.error ? " error" : ""}`;
      const heading = document.createElement("strong");
      heading.textContent = `${workflow.chapter_id} · ${workflow.current_stage}`;
      const stages = document.createElement("span");
      stages.textContent = workflow.stages.map((stage) => `${stage.name}:${stage.status}`).join(" · ");
      row.append(heading, stages);
      wfRoot.append(row);
    });
    if (!workflows.length) wfRoot.textContent = "暂无活动 workflow";
  }
}
