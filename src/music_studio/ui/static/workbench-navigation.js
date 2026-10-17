"use strict";
((root) => {
  const identity = (value) => typeof value === "string" && /^[a-f0-9]{16}$/.test(value) ? value : null;
  function editor(project = null, session = null) {
    const params = new URLSearchParams();
    if (identity(project)) params.set("project", project);
    if (identity(session)) params.set("session", session);
    return "/next.html" + (params.size ? "?" + params : "");
  }
  function workstation(session) {
    return identity(session) ? "/station.html?session=" + session : "/welcome.html";
  }
  const api = { identity, editor, workstation };
  if (typeof module !== "undefined") module.exports = api;
  else root.WorkbenchNavigation = api;
})(typeof window === "undefined" ? globalThis : window);
