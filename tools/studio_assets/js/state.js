/* ===== Application State ===== */

export const state = {
  workspace: null,
  view: "dashboard",
  document: null,
  dirty: false,
  saving: false,
  agent: "goethe",
  continuity: null,
};

export function setWorkspace(data) {
  state.workspace = data;
}

export function setView(name) {
  state.view = name;
}

export function setDocument(doc) {
  state.document = doc;
}

export function setDirty(val) {
  state.dirty = val;
}

export function setSaving(val) {
  state.saving = val;
}

export function setAgent(agent) {
  state.agent = agent;
}

export function setContinuity(data) {
  state.continuity = data;
}
