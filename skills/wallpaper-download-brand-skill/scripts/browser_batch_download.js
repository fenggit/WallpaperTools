const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const ROOT = process.argv[2];
if (!ROOT) {
  console.error("usage: node browser_batch_download.js <brand-root>");
  process.exit(1);
}

const ASSET_EXTS = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".gif",
  ".bmp",
  ".heic",
  ".mp4",
  ".webm",
  ".mov",
  ".m4v",
  ".zip",
  ".rar",
  ".apk",
]);

function readDirSafe(dir) {
  try {
    return fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return [];
  }
}

function hasAssets(dir) {
  return readDirSafe(dir).some(
    entry => entry.isFile() && ASSET_EXTS.has(path.extname(entry.name).toLowerCase())
  );
}

function sourceUrls(dir) {
  const p = path.join(dir, "_source.txt");
  if (!fs.existsSync(p)) return [];
  return fs
    .readFileSync(p, "utf8")
    .split(/\r?\n/)
    .map(s => s.trim())
    .filter(Boolean);
}

async function clickAndDownload(page, outDir) {
  const selectors = [
    '[role="button"]:has-text("全部下载")',
    'button:has-text("全部下载")',
    '[role="button"]:has-text("Download all")',
    'button:has-text("Download all")',
    'button[aria-label="下载"]',
    'button[aria-label="Download"]',
    '[role="button"]:has-text("下载")',
    'button:has-text("下载")',
    '[role="button"]:has-text("Download")',
    'button:has-text("Download")',
  ];

  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    if (!(await locator.count())) continue;
    console.log(`  trying ${selector}`);
    try {
      const [download] = await Promise.all([
        page.waitForEvent("download", { timeout: 90000 }).catch(() => null),
        locator.click({ timeout: 5000, force: true }),
      ]);
      if (download) {
        const suggested = download.suggestedFilename();
        const dest = path.join(outDir, suggested);
        await download.saveAs(dest);
        const ext = path.extname(dest).toLowerCase();
        if (!ASSET_EXTS.has(ext)) {
          try {
            fs.unlinkSync(dest);
          } catch {}
          return null;
        }
        return dest;
      }
    } catch (err) {
      console.log(`  click failed: ${selector}: ${String(err).slice(0, 300)}`);
    }
    await page.waitForTimeout(3000);
  }
  return null;
}

async function downloadSource(context, modelDir, url) {
  const page = await context.newPage();
  try {
    return await Promise.race([
      (async () => {
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 });
        await page.waitForTimeout(5000);
        const title = await page.title().catch(() => "");
        console.log(`  title: ${title}`);
        // Only accept browser-triggered downloads from original source pages.
        return await clickAndDownload(page, modelDir);
      })(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("source timeout after 180s")), 180000)
      ),
    ]);
  } finally {
    await page.close().catch(() => {});
  }
}

async function main() {
  const entries = readDirSafe(ROOT)
    .filter(entry => entry.isDirectory())
    .map(entry => path.join(ROOT, entry.name))
    .filter(dir => !hasAssets(dir) && sourceUrls(dir).length > 0);

  const browser = await chromium.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: [
      "--disable-blink-features=AutomationControlled",
      "--no-first-run",
      "--no-default-browser-check",
      "--lang=zh-CN",
    ],
  });

  const context = await browser.newContext({
    acceptDownloads: true,
    viewport: { width: 1440, height: 1100 },
    locale: "zh-CN",
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
  });

  let success = 0;
  let failed = 0;
  for (let i = 0; i < entries.length; i += 1) {
    const modelDir = entries[i];
    const model = path.basename(modelDir);
    console.log(`[${i + 1}/${entries.length}] ${model}`);
    let ok = false;
    for (const url of sourceUrls(modelDir)) {
      console.log(`  source: ${url}`);
      let downloaded = null;
      try {
        downloaded = await downloadSource(context, modelDir, url);
      } catch (err) {
        console.log(`  source error: ${String(err).slice(0, 500)}`);
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
      if (downloaded) {
        ok = true;
        break;
      }
    }
    if (ok || hasAssets(modelDir)) {
      success += 1;
      console.log("  success");
    } else {
      failed += 1;
      console.log("  failed");
    }
  }

  await browser.close();
  console.log(`done success=${success} failed=${failed}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
