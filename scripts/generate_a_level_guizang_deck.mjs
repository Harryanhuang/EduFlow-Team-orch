import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const mdPath = "/Volumes/Halobster/Obsidian Edu/留学公司知识库/07-公司管理流程通用知识/06-教师培训/A-Level课程体系与升学_首期教师专题研修_杂志风扩展版内容设计稿.md";
const projectDir = path.join(root, "projects/a_level_course_system_admission_guizang");
const htmlPath = path.join(projectDir, "ppt/index.html");

const md = fs.readFileSync(mdPath, "utf8");
let html = fs.readFileSync(htmlPath, "utf8");

const headings = [...md.matchAll(/^## (\d{2}) ([^\n]+)\n/gm)];
const pageMatches = headings
  .filter((m) => Number(m[1]) >= 1 && Number(m[1]) <= 58)
  .map((m, i, arr) => {
    const next = arr[i + 1]?.index ?? md.search(/\n# 三、/);
    const end = next >= 0 ? next : md.length;
    return [m[0], m[1], m[2], md.slice(m.index + m[0].length, end)];
  });
if (pageMatches.length !== 58) {
  throw new Error(`Expected 58 pages, found ${pageMatches.length}`);
}

function esc(s = "") {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function inlineMd(s = "") {
  return esc(s)
    .replace(/`([^`]+)`/g, "<span class=\"mono\">$1</span>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function cleanTitle(s = "") {
  return s.replace(/^章节幕封：/, "").trim();
}

function findField(body, label) {
  const re = new RegExp(`\\*\\*${label}\\*\\*[：:]\\s*\\n\\n([\\s\\S]*?)(?=\\n\\n\\*\\*|\\n---|$)`);
  const m = body.match(re);
  return m ? m[1].trim() : "";
}

function firstQuote(block = "") {
  const lines = block.split("\n").filter((l) => l.trim().startsWith(">"));
  if (!lines.length) return "";
  return lines.map((l) => l.replace(/^\s*>\s?/, "")).join("\n").trim();
}

function firstParagraph(block = "") {
  return block.split(/\n\n+/).map((x) => x.trim()).find((x) => x && !x.startsWith("|") && !x.startsWith("-") && !x.startsWith("```")) || "";
}

function shortLead(s = "", max = 76) {
  const oneLine = s.replace(/\s+/g, " ").trim();
  if (oneLine.length <= max) return oneLine;
  const punctuation = ["。", "；", "，", "、", ".", ";", ","];
  let cut = -1;
  for (const mark of punctuation) {
    const idx = oneLine.lastIndexOf(mark, max);
    if (idx > Math.floor(max * 0.55)) cut = Math.max(cut, idx + 1);
  }
  if (cut < 0) {
    const space = oneLine.lastIndexOf(" ", max);
    cut = space > Math.floor(max * 0.55) ? space : max;
  }
  const trimmed = oneLine.slice(0, cut).replace(/[，。；、：,.:\s]+$/g, "");
  return trimmed + "。";
}

function extractTables(block = "") {
  const lines = block.split("\n");
  const tables = [];
  for (let i = 0; i < lines.length; i++) {
    if (/^\s*\|.*\|\s*$/.test(lines[i]) && i + 1 < lines.length && /^\s*\|[\s:|\-]+\|\s*$/.test(lines[i + 1])) {
      const rows = [];
      rows.push(lines[i]);
      rows.push(lines[i + 1]);
      i += 2;
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        rows.push(lines[i]);
        i++;
      }
      i--;
      const parsed = rows
        .filter((_, idx) => idx !== 1)
        .map((line) => line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
      if (parsed.length > 1) tables.push({ header: parsed[0], rows: parsed.slice(1) });
    }
  }
  return tables;
}

function extractBullets(block = "") {
  return block.split("\n").filter((l) => /^\s*-\s+/.test(l)).map((l) => l.replace(/^\s*-\s+/, "").trim());
}

function pageType(body = "") {
  const raw = findField(body, "页面类型");
  const t = raw.toLowerCase();
  if (t.includes("hero dark")) return "hero dark";
  if (t.includes("hero light")) return "hero light";
  if (t.includes("dark")) return "dark";
  if (t.includes("light")) return "light";
  return "";
}

function fallbackTheme(n) {
  const heroes = new Set([1, 6, 13, 23, 30, 42, 53, 58]);
  if (heroes.has(n)) return n % 2 ? "hero dark" : "hero light";
  return n % 2 ? "dark" : "light";
}

function actLabel(n) {
  if (n <= 5) return "Opening";
  if (n <= 12) return "Act I · System";
  if (n <= 22) return "Act II · CAIE";
  if (n <= 29) return "Act III · IGCSE";
  if (n <= 41) return "Act IV · Selection";
  if (n <= 52) return "Act V · Admission";
  if (n <= 57) return "Act VI · Operation";
  return "Closing";
}

function splitHeroTitle(title) {
  return esc(title).replace(/\n/g, "<br>");
}

function makeChrome(n, title) {
  return `<div class="chrome"><div>${esc(actLabel(n))} · ${esc(cleanTitle(title)).slice(0, 28)}</div><div>${String(n).padStart(2, "0")} / 58</div></div>`;
}

function makeFoot(n) {
  return `<div class="foot"><div>A-Level Course System &amp; Admission</div><div>${String(n).padStart(2, "0")}</div></div>`;
}

function renderRowlines(table, compact = false) {
  const rows = table.rows.slice(0, compact ? 5 : 6);
  const colCount = table.header.length;
  return rows.map((r) => {
    const k = r[0] || "";
    const v = colCount <= 2 ? (r[1] || "") : r.slice(1, -1).join(" · ");
    const m = colCount <= 2 ? table.header[1] || "NOTE" : r[r.length - 1] || table.header.at(-1) || "INFO";
    return `<div class="rowline" data-anim><div class="k">${inlineMd(k)}</div><div class="v">${inlineMd(v)}</div><div class="m">${inlineMd(m)}</div></div>`;
  }).join("\n");
}

function renderCards(table, n) {
  const rows = table.rows.slice(0, 6);
  const cls = rows.length <= 3 ? "grid-3" : rows.length <= 4 ? "grid-4" : "grid-6";
  return `<div class="${cls}" style="margin-top:4vh">\n${rows.map((r) => {
    const head = r[0] || "";
    const note = r.slice(1).join(" · ");
    const isNum = /^[0-9]+[+%]?$|^[0-9]-[0-9]$/.test(head);
    return `<div class="stat-card" data-anim>
      <div class="stat-label">${inlineMd(table.header[0] || "Item")}</div>
      <div class="stat-nb" style="font-size:${isNum ? "5.2vw" : "2.9vw"}">${inlineMd(head)}</div>
      <div class="stat-note">${inlineMd(note)}</div>
    </div>`;
  }).join("\n")}\n</div>`;
}

function renderPipeline(table) {
  const rows = table.rows.slice(0, 6);
  return `<div class="pipeline-section" style="margin-top:4vh"><div class="pipeline-label">${inlineMd(table.header.join(" · "))}</div>
    <div class="pipeline" style="grid-template-columns:repeat(${Math.min(rows.length, 6)},1fr)">
      ${rows.map((r, i) => `<div class="step" data-anim><div class="step-nb">${inlineMd(r[0] || String(i + 1).padStart(2, "0"))}</div><div class="step-title">${inlineMd(r[1] || "")}</div><div class="step-desc">${inlineMd(r.slice(2).join(" · "))}</div></div>`).join("\n")}
    </div></div>`;
}

function renderBullets(bullets) {
  return `<div style="margin-top:4vh">${bullets.slice(0, 6).map((b, i) => `<div class="rowline" data-anim><div class="k">${String(i + 1).padStart(2, "0")}</div><div class="v">${inlineMd(b)}</div><div class="m">POINT</div></div>`).join("\n")}</div>`;
}

function visualHtml(n, body, typeText) {
  const visual = findField(body, "画面内容") || findField(body, "流程内容") || findField(body, "流程") || findField(body, "行动卡") || findField(body, "左侧评价") || "";
  const tables = extractTables(visual);
  const bullets = extractBullets(visual);
  if (tables.length) {
    const t = tables[0];
    const wantsPipeline = /pipeline|时间线|流程|年度/i.test(typeText) || /步骤|阶段|时间|Day|考试季/i.test(t.header.join(" "));
    if (wantsPipeline && t.rows.length <= 4) return renderPipeline(t);
    if (wantsPipeline || t.rows.length > 4) return `<div style="margin-top:3.2vh">${renderRowlines(t, true)}</div>`;
    if (t.rows.length <= 4 || /数据|数字|卡|六宫格|三栏|四卡/i.test(typeText)) return renderCards(t, n);
    return renderRowlines(t, t.rows.length > 6);
  }
  if (bullets.length) return renderBullets(bullets);
  const code = visual.match(/```(?:text)?\n([\s\S]*?)```/);
  if (code) return `<pre class="callout" data-anim style="white-space:pre-wrap;font-family:var(--mono);font-size:1.1vw">${esc(code[1].trim())}</pre>`;
  return "";
}

function renderSlide(match) {
  const n = Number(match[1]);
  const title = cleanTitle(match[2]);
  const body = match[3];
  const typeText = findField(body, "页面类型");
  const theme = pageType(body) || fallbackTheme(n);
  const screenTitle = firstQuote(findField(body, "屏幕主标题")) || title;
  const lead = firstQuote(findField(body, "lead")) || firstParagraph(findField(body, "讲稿展开"));
  const visual = visualHtml(n, body, typeText);
  const titleLen = screenTitle.replace(/\n/g, "").length;
  const rowlineCount = (visual.match(/class="rowline"/g) || []).length;
  let fontSize = titleLen > 20 ? "4.5vw" : titleLen > 13 ? "5.1vw" : theme.includes("hero") ? "7.4vw" : "5.2vw";
  if (!theme.includes("hero") && rowlineCount >= 5) {
    fontSize = titleLen > 18 ? "4.15vw" : "4.65vw";
  }
  if (!theme.includes("hero") && rowlineCount >= 4 && titleLen > 24) {
    fontSize = "3.9vw";
  }

  if (theme.includes("hero")) {
    return `<section class="slide ${theme}" data-theme="${theme.includes("light") ? "light" : "dark"}">
  ${makeChrome(n, title)}
  <div class="frame" style="display:grid;gap:4vh;align-content:center;min-height:80vh">
    <div class="kicker" data-anim>${esc(actLabel(n))}</div>
    <h1 class="h-hero" style="font-size:${fontSize}" data-anim>${splitHeroTitle(screenTitle)}</h1>
    ${lead ? `<p class="lead" style="max-width:62vw" data-anim>${inlineMd(shortLead(lead, 62))}</p>` : ""}
  </div>
  ${makeFoot(n)}
</section>`;
  }

  const tableCount = rowlineCount;
  const contentTop = tableCount >= 5 ? "2vh" : "4vh";
  const leadLimit = tableCount >= 5 ? 58 : 72;
  const leadSize = tableCount >= 5 ? "1.06vw" : "1.18vw";
  const leadLine = tableCount >= 5 ? "1.35" : "1.45";
  return `<section class="slide ${theme}" data-theme="${theme}">
  ${makeChrome(n, title)}
  <div class="frame" style="padding-top:${contentTop}">
    <div class="kicker" data-anim>${esc(title)}</div>
    <h2 class="h-xl" style="font-size:${fontSize}" data-anim>${splitHeroTitle(screenTitle)}</h2>
    ${lead ? `<p class="lead" style="max-width:72vw;margin-top:1.2vh;font-size:${leadSize};line-height:${leadLine}" data-anim>${inlineMd(shortLead(lead, leadLimit))}</p>` : ""}
    ${visual}
  </div>
  ${makeFoot(n)}
</section>`;
}

const slides = pageMatches.map(renderSlide).join("\n\n");

html = html.replace(
  /--ink:#1f1a14;[\s\S]*?--ink-tint:#2d2620;/,
  `--ink:#0a1f3d;
    --ink-rgb:10,31,61;
    --paper:#f1f3f5;
    --paper-rgb:241,243,245;
    --paper-tint:#e4e8ec;
    --ink-tint:#152a4a;`
);
html = html.replace(/<title>[\s\S]*?<\/title>/, "<title>A-Level课程体系与升学 · 桥高国际部首期教师专题研修</title>");
html = html.replace(/<div id="deck">[\s\S]*?<\/div>\s*\n\s*<div id="nav"><\/div>/, `<div id="deck">\n\n${slides}\n\n</div>\n\n<div id="nav"></div>`);

const staticCss = `
  /* 静态蓝白翻页版：保留横向翻页，关闭 WebGL / 入场动效 */
  canvas.bg{display:none!important}
  .slide::before{backdrop-filter:none!important}
  .slide.hero.light::before{background:rgba(var(--paper-rgb),.92)!important}
  .slide.hero.dark::before{background:rgba(var(--ink-rgb),.92)!important}
  .slide.hero::after{display:none!important}
  [data-anim]{opacity:1!important;transform:none!important}
  .slide.dark .rowline{grid-template-columns:minmax(13vw,1.05fr) 2.15fr minmax(12vw,.75fr);padding:1.8vh 0}
  .slide.dark .rowline .k{font-size:2vw;line-height:1.15}
  .slide.dark .rowline .v{font-size:max(16px,1.34vw);line-height:1.45}
  .slide.dark .rowline .m{font-size:max(10px,.68vw);letter-spacing:.14em;line-height:1.35;max-width:18vw;text-align:right}
  .slide.light .rowline{padding:1.7vh 0}
  .slide.light .rowline .v{font-size:max(15px,1.18vw)}
`;
html = html.replace("</style>", `${staticCss}\n</style>`);
html = html.replace(
  /window\.__lowPowerMode = stored === '1' \|\| \(stored === null && reduced\);/,
  "window.__lowPowerMode = true;"
);
html = html.replace(
  /<div id="hint">[\s\S]*?<\/div>/,
  '<div id="hint">← → 翻页 · ESC 索引</div>'
);
html = html.replace(
  /function updateHint\(\)\{[\s\S]*?\n    \}/,
  "function updateHint(){\n      const hint = document.getElementById('hint');\n      if(hint) hint.textContent = '← → 翻页 · ESC 索引';\n    }"
);
html = html.replace(
  /if\(e\.key && e\.key\.toLowerCase\(\)==='b'[\s\S]*?return;\n  \}/,
  "/* Static deck: B key dynamic toggle disabled. */"
);

fs.writeFileSync(htmlPath, html);
console.log(`Generated ${pageMatches.length} slides at ${htmlPath}`);
