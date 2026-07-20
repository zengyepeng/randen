/* ===== Tools View (placeholder for tool-specific logic) ===== */

// Tool operations are initiated from event handlers in app.js.
// Extend tool-specific features here.

/* ===== Creation Engine ===== */

export function initCreationEngine() {
  const bind = (id, handler) => $(`#engine-${id}`)?.addEventListener("click", handler);

  // 扫榜分析
  bind("market", async () => {
    const platform = $("#engine-platform")?.value || "默认";
    const result = $("#engine-market-result");
    if (result) { result.hidden = false; result.textContent = "分析中…"; }
    try {
      const data = await apiPost("/api/market", { platform });
      if (result) {
        result.textContent = data.markets.map(m =>
          `📊 ${m.genre}\n  流量:${m.traffic} 竞争:${m.competition} 新人:${m.newcomer}\n  💡 ${m.tip}`
        ).join("\n\n");
      }
    } catch (e) {
      if (result) result.textContent = `错误: ${e.message}`;
    }
  });

  // 拆书分析
  bind("dissect", async () => {
    const text = $("#engine-dissect-text")?.value || "";
    const title = $("#engine-dissect-title")?.value || "未命名";
    const result = $("#engine-dissect-result");
    if (!text.trim()) { if (result) result.textContent = "请先粘贴正文内容"; return; }
    if (result) { result.hidden = false; result.textContent = "拆解中…"; }
    try {
      const data = await apiPost("/api/dissect", { text, title });
      if (result) {
        result.textContent = `📖 ${data.title}\n章数约: ${data.estimated_chapters} | 字数约: ${data.estimated_words}\n节奏: ${data.rhythm}\n钩子: ${(data.hooks_detected||[]).join(", ")}\n金手指: ${(data.golden_finger_style||[]).join(", ")}\n\n💡 ${data.suggestion}`;
      }
    } catch (e) {
      if (result) result.textContent = `错误: ${e.message}`;
    }
  });

  // 脑洞完善
  bind("idea", async () => {
    const premise = $("#engine-idea-premise")?.value || "";
    const result = $("#engine-idea-result");
    if (!premise.trim()) { if (result) result.textContent = "请先输入灵感"; return; }
    if (result) { result.hidden = false; result.textContent = "分析中…"; }
    try {
      const data = await apiPost("/api/idea", { premise });
      const s = data.setting;
      if (result) {
        result.textContent = `🏷 ${data.genre}\n\n📝 灵感: ${s.premise}\n🎯 金手指: ${s.golden_finger}\n⚠️ 代价: ${s.golden_finger_cost}\n😊 情绪: ${s.target_emotion}\n👤 缺陷: ${s.protagonist_flaw}\n\n📋 还需想清楚:\n${(data.prompt_questions||[]).map(q => "  ❓ "+q).join("\n")}\n\n🚀 下一步:\n${(data.next_steps||[]).map(s => "  → "+s).join("\n")}`;
      }
    } catch (e) {
      if (result) result.textContent = `错误: ${e.message}`;
    }
  });

  // 开篇诊断
  bind("opening", async () => {
    const text = $("#engine-opening-text")?.value || "";
    const result = $("#engine-opening-result");
    if (text.length < 50) { if (result) result.textContent = "请至少粘贴200字开篇"; return; }
    if (result) { result.hidden = false; result.textContent = "诊断中…"; }
    try {
      const data = await apiPost("/api/opening", { text });
      if (result) {
        result.textContent = `⭐ 综合得分: ${data.score}/100\n${data.verdict}\n\n${(data.items||[]).map(i => `${i.passed?"✅":"❌"} ${i.check}${i.passed?"":"\n   → "+i.detail}`).join("\n")}`;
      }
    } catch (e) {
      if (result) result.textContent = `错误: ${e.message}`;
    }
  });

  // FAQ
  loadFAQ();
}

async function loadFAQ() {
  const root = $("#engine-faq");
  if (!root) return;
  try {
    const data = await apiPost("/api/faq", {});
    root.replaceChildren();
    Object.entries(data.faq).forEach(([cat, items]) => {
      const h4 = document.createElement("h4");
      h4.textContent = cat;
      h4.style.cssText = "margin:12px 0 6px;font-size:.9rem";
      root.append(h4);
      items.forEach(item => {
        const chip = document.createElement("span");
        chip.className = "faq-chip";
        chip.textContent = item.q;
        chip.addEventListener("click", () => {
          const existing = root.querySelector(".faq-answer");
          if (existing) existing.remove();
          const ans = document.createElement("div");
          ans.className = "faq-answer";
          ans.textContent = `💬 ${item.a}`;
          chip.after(ans);
        });
        root.append(chip);
      });
    });
  } catch (_) {}
}

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `请求失败 (${res.status})`);
  }
  return res.json();
}
