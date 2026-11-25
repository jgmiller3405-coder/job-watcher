"use strict";

(async () => {
  const { el, number, plural } = JW;
  const $ = (id) => document.getElementById(id);
  const PAGE = 25;

  // Financial analyst postings first, then by employer and title.
  const order = (a, b) =>
    (b.in_role === "true") - (a.in_role === "true") ||
    a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title);

  function list(name, postings, emptyText) {
    const items = $(`${name}-list`), more = $(`${name}-more`);
    const inRole = postings.filter((r) => r.in_role === "true").length;
    $(`${name}-note`).textContent = postings.length
      ? `${plural(postings.length, "posting")}, ${number(inRole)} in the financial analyst role (listed first).`
      : emptyText;
    let shown = 0;
    const showMore = () => {
      for (const row of postings.slice(shown, shown + PAGE)) {
        items.append(JW.postingItem(row, { tags: row.in_role === "true" ? ["Financial analyst"] : [] }));
      }
      shown = Math.min(shown + PAGE, postings.length);
      more.hidden = shown >= postings.length;
      more.textContent = `Show more (${number(postings.length - shown)} left)`;
    };
    more.addEventListener("click", showMore);
    showMore();
  }

  try {
    const { status, rows, runDate } = await JW.data();
    const when = new Date(status.run_time);
    $("run-time").textContent =
      `Last run: ${when.toLocaleString("en-US", { dateStyle: "long", timeStyle: "short" })} your time ` +
      `(${status.run_time.replace("T", " ").replace("Z", " UTC")})`;
    $("days").textContent = number(status.days_with_success);
    $("open").textContent = number(status.open);
    $("new-count").textContent = number(status.new_today);
    $("removed-count").textContent = number(status.removed_today);

    const firstDay = runDate === status.first_run_date;
    list("new", rows.filter((r) => r.first_seen === runDate && r.first_run === "false").sort(order),
      firstDay
        ? "This is the first day of watching. Everything found today was already open, so nothing counts as new yet."
        : "No new postings in the latest run.");
    list("removed", rows.filter((r) => r.removed_date === runDate).sort(order),
      "No postings were removed in the latest run.");

    const employers = new Map(rows.map((r) => [r.source, r.employer]));
    const failed = status.sources.filter((s) => !s.ok).length;
    $("source-note").textContent = failed
      ? `${number(failed)} of ${plural(status.sources.length, "source")} failed. Their postings are left unchanged.`
      : `All ${plural(status.sources.length, "source")} answered. The number is how many postings each returned.`;
    const sorted = [...status.sources].sort((a, b) => a.ok - b.ok || a.name.localeCompare(b.name));
    for (const source of sorted) {
      $("sources").append(el(
        "li", {},
        el("span", { class: "name", text: employers.get(source.name) ?? source.name }),
        el("span", { class: "count", text: number(source.count) }),
        el("span", { class: source.ok ? "state" : "state failed", text: source.ok ? "OK" : "Failed" }),
      ));
    }
  } catch (error) {
    $("run-time").textContent = "";
    JW.showError(error);
  }
})();
