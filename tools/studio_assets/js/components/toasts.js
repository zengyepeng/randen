/* ===== Toast Notification Component ===== */

// Toast functionality is in utils.js — this module provides
// programmatic toast queue management for future expansion.

let queue = [];
let active = false;

export function showToast(message, error = false) {
  // Delegates to utils.js showToast for now
  import("../utils.js").then((m) => m.showToast(message, error));
}

export function queueToast(message, error = false, delay = 300) {
  queue.push({ message, error });
  if (!active) flushQueue(delay);
}

async function flushQueue(delay) {
  active = true;
  const { showToast } = await import("../utils.js");
  while (queue.length) {
    const item = queue.shift();
    showToast(item.message, item.error);
    await new Promise((r) => setTimeout(r, delay + 2600));
  }
  active = false;
}
