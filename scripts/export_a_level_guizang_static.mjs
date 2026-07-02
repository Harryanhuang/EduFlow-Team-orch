import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const pptxgen = require("pptxgenjs");
const { PDFDocument } = require("pdf-lib");

const root = process.cwd();
const projectDir = path.join(root, "projects/a_level_course_system_admission_guizang");
const htmlPath = path.join(projectDir, "ppt/index.html");
const exportDir = path.join(projectDir, "exports/blue_porcelain_static");
const pngDir = path.join(exportDir, "slides_png");
const pptxPath = path.join(exportDir, "A-Level课程体系与升学_桥高国际部首期教师专题研修_靛蓝瓷静态版.pptx");
const pdfPath = path.join(exportDir, "A-Level课程体系与升学_桥高国际部首期教师专题研修_靛蓝瓷静态版.pdf");

fs.mkdirSync(pngDir, { recursive: true });

const chromeCandidates = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/Users/huanganan/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell"
];
const executablePath = chromeCandidates.find((p) => fs.existsSync(p));
const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
await page.addStyleTag({
  content: `
    #nav,#hint{display:none!important}
    canvas.bg{display:none!important}
    *{animation:none!important;transition:none!important}
    [data-anim]{opacity:1!important;transform:none!important}
  `
});

const total = await page.$$eval("section.slide", (els) => els.length);
if (total !== 58) throw new Error(`Expected 58 slides, got ${total}`);

const images = [];
for (let i = 0; i < total; i++) {
  await page.evaluate((idx) => {
    window.go(idx);
    document.body.classList.add("low-power");
  }, i);
  await page.waitForTimeout(80);
  const out = path.join(pngDir, `slide-${String(i + 1).padStart(2, "0")}.png`);
  await page.screenshot({ path: out, fullPage: false });
  images.push(out);
}
await browser.close();

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "EduFlow";
pptx.subject = "A-Level 课程体系与升学";
pptx.title = "A-Level课程体系与升学";
pptx.company = "桥高国际部";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Noto Serif SC",
  bodyFontFace: "Noto Sans SC",
  lang: "zh-CN"
};
for (const img of images) {
  const slide = pptx.addSlide();
  slide.background = { color: "F1F3F5" };
  slide.addImage({ path: img, x: 0, y: 0, w: 13.333333, h: 7.5 });
}
await pptx.writeFile({ fileName: pptxPath });

const pdf = await PDFDocument.create();
for (const img of images) {
  const bytes = fs.readFileSync(img);
  const png = await pdf.embedPng(bytes);
  const pagePdf = pdf.addPage([1600, 900]);
  pagePdf.drawImage(png, { x: 0, y: 0, width: 1600, height: 900 });
}
fs.writeFileSync(pdfPath, await pdf.save());

console.log(JSON.stringify({ total, pptxPath, pdfPath, pngDir }, null, 2));
