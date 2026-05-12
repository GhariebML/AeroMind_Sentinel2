import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const urlArgIndex = process.argv.indexOf('--url');
const baseUrl = urlArgIndex >= 0 ? process.argv[urlArgIndex + 1] : process.env.VERCEL_URL || process.env.SENTINEL_CAPTURE_URL;

if (!baseUrl) {
  console.error('Missing deployment URL. Usage: npm run capture:screenshots -- --url https://your-vercel-url.vercel.app');
  process.exit(1);
}

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.error('Playwright is not installed. Run: npm install');
  process.exit(1);
}

const outputDir = path.resolve('docs/screenshots');
await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });

const shots = [
  ['01_home_hero.png', '/'],
  ['02_live_simulation.png', '/#simulation'],
  ['03_metrics.png', '/#metrics'],
  ['04_business_model.png', '/#business'],
  ['05_pitch_export.png', '/pitch'],
];

for (const [filename, route] of shots) {
  const target = new URL(route, baseUrl).toString();
  await page.goto(target, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(outputDir, filename), fullPage: filename.includes('pitch') });
  console.log(`Captured ${filename} from ${target}`);
}

await browser.close();
console.log(`Screenshots saved to ${outputDir}`);
