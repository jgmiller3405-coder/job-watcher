// Shared by all three pages: loading the data files and building page elements.
"use strict";

const JW = (() => {
  // Minimal CSV reader that handles quoted fields, doubled quotes, and newlines.
  function parseCSV(text) {
    const records = [];
    let record = [], field = "", quoted = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (quoted) {
        if (c !== '"') field += c;
        else if (text[i + 1] === '"') { field += '"'; i++; }
        else quoted = false;
      } else if (c === '"') quoted = true;
      else if (c === ",") { record.push(field); field = ""; }
      else if (c === "\n") { record.push(field); records.push(record); record = []; field = ""; }
      else if (c !== "\r") field += c;
    }
    if (field !== "" || record.length) { record.push(field); records.push(record); }
    const [header = [], ...rows] = records;
    return rows.map((r) => Object.fromEntries(header.map((name, i) => [name, r[i] ?? ""])));
  }

  async function load(path) {
    const response = await fetch(path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return response;
  }

  // Both data files, plus the UTC date of the latest run.
  async function data() {
    const [status, csv] = await Promise.all([
      load("data/status.json").then((r) => r.json()),
      load("data/history.csv").then((r) => r.text()),
    ]);
    return { status, rows: parseCSV(csv), runDate: status.run_time.slice(0, 10) };
  }

  const DAY = 86400000;
  const dayNumber = (date) => Date.parse(`${date}T00:00:00Z`) / DAY;
  const daysBetween = (from, to) => Math.round(dayNumber(to) - dayNumber(from));
  const addDays = (date, n) => new Date((dayNumber(date) + n) * DAY).toISOString().slice(0, 10);
  const shortDate = (date) =>
    new Date(`${date}T00:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
  const number = (n) => n.toLocaleString("en-US");
  const plural = (n, word) => `${number(n)} ${word}${n === 1 ? "" : "s"}`;

  // Create an element. Text is always set as text, never as HTML.
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (key === "text") node.textContent = value;
      else node.setAttribute(key, value);
    }
    node.append(...children.filter((c) => c !== null && c !== undefined));
    return node;
  }

  const safeURL = (url) => (/^https?:\/\//i.test(url) ? url : "#");

  function postingItem(row, { meta, before, tags = [] } = {}) {
    const title = el("div", { class: "title", text: row.title });
    for (const tag of tags) title.append(el("span", { class: "tag", text: tag }));
    const details = [row.employer, row.location, row.department, meta].filter(Boolean).join(" · ");
    return el(
      "li", { class: "posting" },
      before,
      el("div", { class: "body" }, title, el("div", { class: "meta", text: details })),
      el("a", {
        class: "apply", href: safeURL(row.url), target: "_blank", rel: "noopener",
        "aria-label": `Apply: ${row.title} at ${row.employer}`, text: "Apply ↗",
      }),
    );
  }

  function showError(error) {
    console.error(error);
    document.querySelector("main").prepend(
      el("div", { class: "notice", role: "alert", text: `The data could not be loaded. ${error.message}` }),
    );
  }

  function offlineNotice() {
    let notice = null;
    const update = () => {
      if (!navigator.onLine && !notice) {
        notice = el("div", { class: "notice", text: "You are offline. Showing the last data loaded." });
        document.querySelector("main").prepend(notice);
      } else if (navigator.onLine && notice) { notice.remove(); notice = null; }
    };
    addEventListener("online", update);
    addEventListener("offline", update);
    update();
  }

  offlineNotice();
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch((error) => console.warn(error));
  }

  return { data, parseCSV, daysBetween, addDays, shortDate, number, plural, el, postingItem, showError };
})();
