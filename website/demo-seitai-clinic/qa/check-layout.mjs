import { createRequire } from "node:module";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("C:/Users/hangy/AppData/Roaming/npm/node_modules/playwright");
const qaDir = dirname(fileURLToPath(import.meta.url));
const projectDir = resolve(qaDir, "..");
const pageUrl = pathToFileURL(resolve(projectDir, "index.html")).href;
const widths = [375, 599, 600, 768, 959, 960, 1440];
const results = [];

await mkdir(resolve(qaDir, "screenshots"), { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
});

for (const width of widths) {
  const page = await browser.newPage({ viewport: { width, height: width < 600 ? 812 : 900 } });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(pageUrl, { waitUntil: "load" });
  const images = page.locator("img");
  for (let index = 0; index < await images.count(); index += 1) {
    await images.nth(index).scrollIntoViewIfNeeded();
  }
  await page.waitForFunction(() => [...document.images].every((image) => image.complete));
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(250);

  const state = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    viewportWidth: document.documentElement.clientWidth,
    h1Count: document.querySelectorAll("h1").length,
    missingImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).map((image) => image.src),
    visibleMenuButton: getComputedStyle(document.querySelector(".menu-button")).display !== "none",
  }));

  if (width === 375 || width === 1440) {
    await page.screenshot({
      path: resolve(qaDir, "screenshots", `homepage-${width}.png`),
      fullPage: true,
    });
  }

  if (width === 375) {
    await page.locator(".menu-button").click();
    await page.waitForTimeout(300);
    state.mobileMenuOpened = await page.locator(".global-nav").evaluate((element) => element.classList.contains("is-open"));
    await page.screenshot({
      path: resolve(qaDir, "screenshots", "menu-open-375.png"),
    });
    await page.keyboard.press("Escape");
    state.mobileMenuClosedWithEscape = await page.locator(".global-nav").evaluate((element) => !element.classList.contains("is-open"));
  }

  results.push({ width, ...state, pageErrors: errors });
  await page.close();
}

await browser.close();
console.log(JSON.stringify(results, null, 2));

const failed = results.some((result) =>
  result.documentWidth > result.viewportWidth ||
  result.h1Count !== 1 ||
  result.missingImages.length > 0 ||
  result.pageErrors.length > 0 ||
  (result.width < 960 && !result.visibleMenuButton) ||
  (result.width >= 960 && result.visibleMenuButton) ||
  (result.width === 375 && (!result.mobileMenuOpened || !result.mobileMenuClosedWithEscape))
);

process.exitCode = failed ? 1 : 0;
