// Every number on this page is computed here from data/history.csv.
"use strict";

(async () => {
  const { number, plural, shortDate, daysBetween, addDays } = JW;
  const ALL = "var(--series-all)", ROLE = "var(--series-role)";

  function section(id, heading, text) {
    const node = document.getElementById(id);
    node.querySelector("h2").textContent = heading;
    node.querySelector("p").textContent = text;
    return node.querySelector(".chart");
  }
  const countBy = (rows, key) => {
    const counts = new Map();
    for (const row of rows) counts.set(row[key], (counts.get(row[key]) ?? 0) + 1);
    return counts;
  };
  const ranked = (counts) =>
    [...counts].map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value || a.label.localeCompare(b.label));
  const median = (values) => {
    const s = [...values].sort((a, b) => a - b), mid = Math.floor(s.length / 2);
    return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
  };
  const percent = (part, whole) => `${Math.round((100 * part) / whole)}%`;
  const oneDecimal = (n) => n.toLocaleString("en-US", { maximumFractionDigits: 1 });

  try {
    const { status, rows, runDate } = await JW.data();
    const start = rows.reduce((min, r) => (r.first_seen < min ? r.first_seen : min), runDate);
    const dates = Array.from({ length: daysBetween(start, runDate) + 1 }, (_, i) => addDays(start, i));
    const later = dates.length - 1; // days on which something could be new or removed
    const open = rows.filter((r) => r.status === "open");
    const series = (subset, key) => {
      const counts = countBy(subset, key);
      return dates.map((d) => ({ label: shortDate(d), full: d, value: counts.get(d) ?? 0 }));
    };

    document.getElementById("coverage").textContent =
      `${plural(rows.length, "posting")} tracked from ${start} to ${runDate}, ` +
      `with a successful run on ${plural(status.days_with_success, "day")}.`;

    // 1. New postings per day
    const fresh = rows.filter((r) => r.first_run === "false");
    const freshRole = fresh.filter((r) => r.in_role === "true");
    let chart = section(
      "s-new",
      later === 0 ? "New postings will appear after the second day of watching"
        : `${oneDecimal(fresh.length / later)} new postings a day on average, ${oneDecimal(freshRole.length / later)} in the financial analyst role`,
      `Since ${start}, ${plural(fresh.length, "posting")} appeared that ${fresh.length === 1 ? "was" : "were"} not there when watching began; ` +
      `${number(freshRole.length)} matched the financial analyst title rule. The averages cover the ${plural(later, "day")} after the first. ` +
      "Postings already open in a source's first file are left out. The two charts have separate scales.",
    );
    Charts.columns(chart, series(fresh, "first_seen"), { title: "All postings", color: ALL, heading: "Date", unit: "New postings" });
    Charts.columns(chart, series(freshRole, "first_seen"), { title: "Financial analyst", color: ROLE, heading: "Date", unit: "New postings" });

    // 2. Removed postings per day
    const removed = rows.filter((r) => r.removed_date !== "");
    const removedRole = removed.filter((r) => r.in_role === "true").length;
    chart = section(
      "s-removed",
      later === 0 ? "Removals will appear after the second day of watching"
        : `${oneDecimal(removed.length / later)} postings removed a day on average`,
      `${plural(removed.length, "posting")} ${removed.length === 1 ? "is" : "are"} currently marked removed, ${number(removedRole)} of them financial analyst roles. ` +
      "A posting counts on the day its employer's board stopped listing it. If it is listed again, it returns to open and drops out of this chart.",
    );
    Charts.columns(chart, series(removed, "removed_date"), { color: ALL, heading: "Date", unit: "Removed postings" });

    // 3. Open postings per employer
    const employers = ranked(countBy(open, "employer"));
    const top = employers[0];
    const openRole = open.filter((r) => r.in_role === "true").length;
    chart = section(
      "s-employers",
      top ? `${top.label} has the most open postings: ${number(top.value)} of ${number(open.length)}` : "No postings are open",
      `As of the ${runDate} run, ${plural(open.length, "posting")} ${open.length === 1 ? "is" : "are"} open across ${plural(employers.length, "employer")}, ` +
      `${number(openRole)} of them financial analyst roles. JPMorgan Chase, H&R Block, and Ulta Beauty are collected with ` +
      "the search term “analyst”, so their bars cover only the postings that search returns.",
    );
    Charts.bars(chart, employers, { label: "Open postings per employer" });

    // 4. Days open
    const durations = removed.filter((r) => r.first_run === "false")
      .map((r) => daysBetween(r.first_seen, r.removed_date));
    const mid = durations.length ? median(durations) : null;
    chart = section(
      "s-days",
      mid === null ? "No newly posted job has been removed yet"
        : `Removed postings stayed open a median of ${oneDecimal(mid)} ${mid === 1 ? "day" : "days"}`,
      mid === null
        ? "This needs a posting that first appeared after watching began and was later removed."
        : `Based on ${plural(durations.length, "removed posting")} that first appeared after watching began. ` +
          "Days open is the removed date minus the first-seen date. With a short history, only short-lived postings can have finished, " +
          "so the median will tend to rise as the history grows.",
    );
    if (durations.length) {
      const longest = durations.reduce((a, b) => Math.max(a, b), 1);
      const cap = Math.min(longest, 30);
      const points = Array.from({ length: cap }, (_, i) => {
        const days = i + 1, last = days === cap && longest > cap;
        return {
          label: last ? `${days}+` : String(days),
          full: last ? `${days} days or more` : plural(days, "day"),
          value: durations.filter((d) => (last ? d >= days : d === days)).length,
        };
      });
      Charts.columns(chart, points, { title: "Removed postings by days open", color: ALL, heading: "Days open", unit: "Postings" });
    }

    // 5. Share removed within seven days
    const cutoff = addDays(runDate, -7);
    const eligible = fresh.filter((r) => r.first_seen <= cutoff);
    const quick = eligible.filter((r) => r.removed_date !== "" && daysBetween(r.first_seen, r.removed_date) <= 7).length;
    chart = section(
      "s-week",
      eligible.length ? `${percent(quick, eligible.length)} of new postings were removed within seven days`
        : "Not enough history yet to judge the first week",
      eligible.length
        ? `Of ${plural(eligible.length, "posting")} first seen on or before ${cutoff} (leaving out first-run postings), ` +
          `${number(quick)} ${quick === 1 ? "was" : "were"} removed seven days or less after first appearing.`
        : "This counts postings that first appeared after watching began and at least seven days before the latest run. " +
          `The earliest it can have an answer is ${addDays(start, 8)}.`,
    );
    if (eligible.length) {
      const rest = eligible.length - quick;
      Charts.bars(chart, [
        { label: "Removed within 7 days", value: quick, note: `${number(quick)} (${percent(quick, eligible.length)})` },
        { label: "Lasted longer", value: rest, note: `${number(rest)} (${percent(rest, eligible.length)})` },
      ], { label: "Postings by whether they were removed within seven days" });
    }

    // 6. Top locations
    // Some boards give only a count such as "3 Locations", which names no place.
    const named = open.filter((r) => r.location !== "" && !/^\d+ Locations?$/i.test(r.location));
    const places = ranked(countBy(named, "location")).slice(0, 10);
    chart = section(
      "s-places",
      places.length ? `${places[0].label} is the most common location, with ${plural(places[0].value, "open posting")}` : "No locations to rank",
      `The ten most common locations among open postings, as each employer writes them, so one city can appear under more than one spelling. ` +
      `${plural(open.length - named.length, "open posting")} with no location, or only a count such as “3 Locations”, ` +
      `${open.length - named.length === 1 ? "is" : "are"} left out.`,
    );
    Charts.bars(chart, places, { label: "Top locations among open postings" });
  } catch (error) {
    document.getElementById("coverage").textContent = "";
    JW.showError(error);
  }
})();
