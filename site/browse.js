"use strict";

(async () => {
  const { el, number, plural } = JW;
  const $ = (id) => document.getElementById(id);
  const PAGE = 50;
  const KEY = "jobwatcher.shortlist";

  // The shortlist lives in this browser's local storage.
  function readStars() {
    try { return new Set(JSON.parse(localStorage.getItem(KEY) ?? "[]")); }
    catch { return new Set(); }
  }
  function saveStars() {
    try { localStorage.setItem(KEY, JSON.stringify([...stars])); }
    catch (error) { console.warn("The shortlist could not be saved.", error); }
  }
  let stars = readStars();

  let loaded;
  try { loaded = await JW.data(); }
  catch (error) { $("result-count").textContent = ""; JW.showError(error); return; }
  const { rows, runDate } = loaded;
  for (const row of rows) row.age = JW.daysBetween(row.first_seen, runDate);

  const open = rows.filter((r) => r.status === "open");
  let scope = "role", matches = [], shown = 0;

  for (const name of [...new Set(open.map((r) => r.employer))].sort((a, b) => a.localeCompare(b))) {
    $("employer").append(el("option", { value: name, text: name }));
  }
  const places = new Map();
  for (const r of open) if (r.location) places.set(r.location, (places.get(r.location) ?? 0) + 1);
  for (const [place] of [...places].sort((a, b) => b[1] - a[1]).slice(0, 500)) {
    $("locations").append(el("option", { value: place }));
  }

  function starButton(row) {
    const button = el("button", { type: "button", class: "star" });
    const paint = () => {
      const on = stars.has(row.posting_id);
      button.textContent = on ? "★" : "☆";
      button.setAttribute("aria-pressed", String(on));
      button.setAttribute("aria-label", `${on ? "Remove from" : "Save to"} shortlist: ${row.title}`);
    };
    button.addEventListener("click", () => {
      stars = readStars(); // another tab may have changed it
      if (!stars.delete(row.posting_id)) stars.add(row.posting_id);
      saveStars();
      paint();
      countStars();
    });
    paint();
    return button;
  }

  function countStars() {
    $("star-count").textContent = number(rows.filter((r) => stars.has(r.posting_id)).length);
  }

  function showMore() {
    for (const row of matches.slice(shown, shown + PAGE)) {
      const age = `${row.first_run === "true" ? "at least " : ""}${plural(row.age, "day")}`;
      const tags = row.status === "removed" ? [`Removed ${row.removed_date}`] : [];
      $("results").append(JW.postingItem(row, {
        before: starButton(row), tags, meta: `First seen ${row.first_seen} · open ${age}`,
      }));
    }
    shown = Math.min(shown + PAGE, matches.length);
    $("more").hidden = shown >= matches.length;
    $("more").textContent = `Show more (${number(matches.length - shown)} left)`;
  }

  function apply() {
    const saved = $("shortlist").checked;
    const words = $("search").value.trim().toLowerCase();
    const employer = $("employer").value;
    const place = $("location").value.trim().toLowerCase();
    const [kind, limit] = $("age").value.split(":");
    const direction = $("sort").value === "newest" ? -1 : 1;
    // The shortlist shows every saved posting, including ones since removed.
    $("scope-role").disabled = $("scope-all").disabled = saved;

    matches = (saved ? rows.filter((r) => stars.has(r.posting_id)) : open).filter((r) =>
      (saved || scope === "all" || r.in_role === "true") &&
      (!words || r.title.toLowerCase().includes(words)) &&
      (!employer || r.employer === employer) &&
      (!place || r.location.toLowerCase().includes(place)) &&
      (kind !== "max" || (r.first_run === "false" && r.age <= Number(limit))) &&
      (kind !== "min" || r.age >= Number(limit)),
    ).sort((a, b) =>
      direction * a.first_seen.localeCompare(b.first_seen) ||
      a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title),
    );

    $("results").replaceChildren();
    shown = 0;
    const what = saved ? "saved posting" : scope === "role" ? "open financial analyst posting" : "open posting";
    $("result-count").textContent = matches.length
      ? plural(matches.length, what)
      : saved ? "Nothing saved matches. Star a posting to add it to your shortlist."
        : "No open postings match these filters.";
    showMore();
  }

  function setScope(next) {
    scope = next;
    $("scope-role").setAttribute("aria-pressed", String(next === "role"));
    $("scope-all").setAttribute("aria-pressed", String(next === "all"));
    apply();
  }

  $("scope-role").addEventListener("click", () => setScope("role"));
  $("scope-all").addEventListener("click", () => setScope("all"));
  for (const id of ["search", "location"]) $(id).addEventListener("input", apply);
  for (const id of ["employer", "age", "sort", "shortlist"]) $(id).addEventListener("change", apply);
  $("reset").addEventListener("click", () => {
    for (const id of ["search", "location", "employer", "age"]) $(id).value = "";
    $("sort").value = "newest";
    $("shortlist").checked = false;
    setScope("role");
  });
  $("more").addEventListener("click", showMore);
  addEventListener("storage", () => { stars = readStars(); countStars(); apply(); });

  countStars();
  apply();
})();
