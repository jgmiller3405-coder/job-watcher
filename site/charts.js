// Small hand-written charts, so the site needs nothing from other servers.
"use strict";

const Charts = (() => {
  const { el, number } = JW;
  const SVG = "http://www.w3.org/2000/svg";

  function svg(tag, attrs, text) {
    const node = document.createElementNS(SVG, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function table(headings, rows) {
    return el(
      "details", {},
      el("summary", { text: "Show as a table" }),
      el(
        "table", {},
        el("thead", {}, el("tr", {}, ...headings.map((h) => el("th", { scope: "col", text: h })))),
        el("tbody", {}, ...rows.map((r) => el("tr", {}, ...r.map((v) => el("td", { text: String(v) }))))),
      ),
    );
  }

  // A round number at or above the largest value, split into four or fewer steps.
  function scale(max) {
    const rough = Math.max(max, 1) / 4;
    const power = 10 ** Math.floor(Math.log10(rough));
    const step = Math.max(1, [1, 2, 5, 10].map((m) => m * power).find((s) => s >= rough));
    return { step, top: Math.max(step, Math.ceil(max / step) * step) };
  }

  // Vertical columns. points: [{label, full, value}]
  function columns(parent, points, { title, color, heading, unit }) {
    const frame = el("div", { class: "chart" });
    if (title) frame.append(el("h3", { text: title }));
    const plot = el("div", { style: "position:relative" });
    const tip = el("div", { class: "tooltip", hidden: "" });
    frame.append(plot, table([heading, unit], points.map((p) => [p.full, p.value])));
    parent.append(frame);

    function draw() {
      const width = Math.max(plot.clientWidth, 260), height = 200;
      const left = 44, right = 8, top = 18, bottom = 24;
      const innerW = width - left - right, innerH = height - top - bottom;
      const { step, top: max } = scale(Math.max(0, ...points.map((p) => p.value)));
      const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": title ?? unit });
      const y = (v) => top + innerH - (v / max) * innerH;
      for (let v = 0; v <= max; v += step) {
        root.append(
          svg("line", { x1: left, x2: width - right, y1: y(v), y2: y(v), class: v ? "grid" : "axis" }),
          svg("text", { x: left - 8, y: y(v) + 4, "text-anchor": "end" }, number(v)),
        );
      }
      const band = innerW / points.length;
      const bar = Math.max(1, Math.min(24, band - 2));
      const every = Math.max(1, Math.ceil(points.length / Math.floor(innerW / 60)));
      const largest = points.reduce((best, p, i) => (p.value > points[best].value ? i : best), 0);
      points.forEach((p, i) => {
        const x = left + band * i + (band - bar) / 2;
        const h = (p.value / max) * innerH;
        if (h > 0) {
          const r = Math.min(4, bar / 2, h), base = top + innerH;
          root.append(svg("path", {
            fill: color,
            d: `M${x},${base}V${base - h + r}Q${x},${base - h} ${x + r},${base - h}` +
               `H${x + bar - r}Q${x + bar},${base - h} ${x + bar},${base - h + r}V${base}Z`,
          }));
        }
        // Label only the tallest column and the latest one.
        if (p.value > 0 && (i === largest || i === points.length - 1)) {
          root.append(svg("text", { x: x + bar / 2, y: y(p.value) - 5, "text-anchor": "middle" }, number(p.value)));
        }
        if ((points.length - 1 - i) % every === 0) {
          root.append(svg("text", { x: x + bar / 2, y: height - 6, "text-anchor": "middle" }, p.label));
        }
        const hit = svg("rect", {
          x: left + band * i, y: top, width: band, height: innerH, class: "hit",
          tabindex: 0, "aria-label": `${p.full}: ${p.value}`,
        });
        const show = () => {
          tip.textContent = `${number(p.value)} · ${p.full}`;
          tip.hidden = false;
          const half = tip.offsetWidth / 2;
          tip.style.left = `${Math.min(Math.max(x + bar / 2, half), width - half)}px`;
          tip.style.top = `${Math.max(y(p.value), 28)}px`;
        };
        const hide = () => { tip.hidden = true; };
        hit.addEventListener("pointerenter", show);
        hit.addEventListener("focus", show);
        hit.addEventListener("pointerleave", hide);
        hit.addEventListener("blur", hide);
        root.append(hit);
      });
      tip.hidden = true;
      plot.replaceChildren(root, tip);
    }

    draw();
    let last = plot.clientWidth;
    new ResizeObserver(() => {
      if (plot.clientWidth !== last) { last = plot.clientWidth; draw(); }
    }).observe(plot);
  }

  // Horizontal bars with the value written at the end of each. items: [{label, value, note}]
  function bars(parent, items, { label }) {
    const max = Math.max(1, ...items.map((i) => i.value));
    parent.append(el(
      "ul", { class: "hbars", "aria-label": label },
      ...items.map((item) => el(
        "li", {},
        el("span", { class: "name", text: item.label }),
        el(
          "span", { class: "track" },
          // Stopping at 75% leaves room for the number beside the longest bar.
          el("span", { class: "bar", style: `width:${(item.value / max) * 75}%` }),
          el("span", { class: "num", text: item.note ?? number(item.value) }),
        ),
      )),
    ));
  }

  return { columns, bars };
})();
