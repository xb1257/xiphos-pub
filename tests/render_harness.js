/* Minimaler DOM-Stub, um den Renderer aus index.html ohne Browser zu pruefen.
   Prueft die kritischen Punkte: Tagesgruppierung in der Geraetezeitzone,
   ganztaegig zuerst, Live-/Done-Ableitung, Filter, leere Tage. */
const fs = require("fs");

function makeNode(tag) {
  return {
    tag, className: "", _text: "", children: [], attrs: {},
    set textContent(v) { this._text = v; this.children = []; },
    get textContent() { return this._text; },
    appendChild(c) { this.children.push(c); return c; },
    get childNodes() { return this.children; },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k]; },
    addEventListener() {},
    querySelectorAll() { return []; },
    classList: { toggle() { return true; }, add() {}, remove() {} },
    set href(v) { this.attrs.href = v; },
    set target(v) {}, set rel(v) {}, set type(v) {},
  };
}
function text(n) {
  if (!n) return "";
  let s = n._text || "";
  for (const c of n.children) s += text(c);
  return s;
}
function dump(n, depth = 0) {
  const out = [];
  const own = (n._text || "").trim();
  out.push("  ".repeat(depth) + n.tag + (n.className ? "." + n.className.replace(/ /g, ".") : "") + (own ? " «" + own + "»" : ""));
  for (const c of n.children) out.push(...dump(c, depth + 1));
  return out;
}

const ids = {};
for (const id of ["cal", "foot", "warn", "filters", "filterbar", "ftoggle", "fstate", "tz", "stand"]) {
  ids[id] = makeNode("div");
}
global.document = {
  createElement: makeNode,
  createTextNode: (t) => ({ tag: "#text", className: "", _text: t, children: [] }),
  getElementById: (id) => ids[id],
  addEventListener() {},
  hidden: false,
};
const store = {};
if (process.env.HIDE) store["sportcal.hidden"] = JSON.stringify(
  Object.fromEntries(process.env.HIDE.split(",").map((k) => [k, true])));
global.localStorage = {
  getItem: (k) => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = v; },
};
const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
global.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) });
global.setInterval = () => 0;

const html = fs.readFileSync("index.html", "utf8");
let js = html.match(/<script>([\s\S]*)<\/script>/)[1];
// Debug: verschluckte Render-Fehler sichtbar machen
js = js.replace(/catch\((err|e)\)\{/g, (m, v) => "catch(" + v + "){if(process.env.DEBUG_JS)console.error('ERR', " + v + ");");
eval(js);

setTimeout(() => {
  const days = ids.cal.children;
  console.log("TZ=" + Intl.DateTimeFormat().resolvedOptions().timeZone + "  Sections=" + days.length);
  for (const sec of days) {
    const head = text(sec.children[0]).replace(/\s+/g, " ");
    const rows = sec.children.slice(1);
    console.log("\n== " + head + (sec.className.includes("today") ? "   [today-Kante]" : ""));
    for (const r of rows.slice(0, 4)) {
      console.log("   " + (r.className || "").padEnd(34) + " | " + text(r).replace(/\s+/g, " ").slice(0, 88));
    }
    if (rows.length > 4) console.log("   ... +" + (rows.length - 4) + " weitere");
  }
  console.log("\nHeader: " + text(ids.tz) + " / " + text(ids.stand));
  console.log("Filter-Zustand: " + text(ids.fstate));
  console.log("Chips: " + ids.filters.children.length);
  console.log("Footer: " + text(ids.foot).replace(/\s+/g, " "));
  console.log("Warn: " + (text(ids.warn) || "-"));
}, 50);
