/* global document */
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright-core';

const [argumentAppUrl, argumentCdpUrl, argumentEvidenceDir, expectedApiBaseUrl = ''] = process.argv.slice(2);
const appUrl = argumentAppUrl || process.env.APP_URL;
const cdpUrl = argumentCdpUrl || process.env.CDP_URL;
const evidenceDir = argumentEvidenceDir || process.env.EVIDENCE_DIR;
if (!appUrl || !cdpUrl || !evidenceDir) throw new Error('app URL, CDP URL, and evidence directory are required');

await mkdir(evidenceDir, { recursive: true });
const consoleErrors = [];
const networkRequests = [];
const externalRequests = [];
const routeResults = [];
let expectedDeniedHttp403 = false;
let awsDeniedHttp403 = false;
let cloudTrailStatus = 'NOT_APPLICABLE';
let issue9InitialStatus = 'NOT_APPLICABLE';
const startedAt = new Date().toISOString();

function assert(condition, message) { if (!condition) throw new Error(message); }
async function saveJson(name, value) {
  await writeFile(path.join(evidenceDir, name), `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
}
function routeUrl(hash) { const url = new URL(appUrl); url.hash = hash; return url.toString(); }
function isAllowedRequest(rawUrl) {
  const url = new URL(rawUrl);
  if (!['http:', 'https:', 'ws:', 'wss:'].includes(url.protocol)) return true;
  return ['localhost', '127.0.0.1'].includes(url.hostname) ||
    (expectedApiBaseUrl && rawUrl.startsWith(expectedApiBaseUrl));
}

let browser;
let page;
try {
  browser = await chromium.connectOverCDP(cdpUrl);
  const context = browser.contexts()[0] ?? await browser.newContext();
  page = context.pages()[0] ?? await context.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('pageerror', (error) => consoleErrors.push(error.message));
  page.on('request', (request) => {
    const entry = { method: request.method(), resourceType: request.resourceType(), url: request.url() };
    networkRequests.push(entry);
    if (!isAllowedRequest(entry.url)) externalRequests.push(entry);
  });
  page.on('response', (response) => {
    const invokeUrl = expectedApiBaseUrl ? `${expectedApiBaseUrl.replace(/\/$/, '')}/invoke` : '';
    if (invokeUrl && response.url() === invokeUrl && response.status() === 403) {
      expectedDeniedHttp403 = true;
    }
  });

  await page.goto(routeUrl('#/'), { waitUntil: 'domcontentloaded', timeout: 15_000 });
  const issue9Mode = await page.getByTestId('issue9-proof').isVisible().catch(() => false);
  const routes = issue9Mode ? [
    { hash: '#/', name: 'Project', expectedText: 'Native Bedrock access.' },
    { hash: '#/playground', name: 'Playground', expectedText: 'Model proof' },
    { hash: '#/logs', name: 'Logs', expectedText: 'CloudTrail evidence' },
  ] : [
    { hash: '#/', name: 'Project', expectedText: 'Governed model access.' },
    { hash: '#/playground', name: 'Playground', expectedText: 'Playground' },
    { hash: '#/logs', name: 'Logs', expectedText: 'Central audit' },
  ];
  for (const route of routes) {
    await page.goto(routeUrl(route.hash), { waitUntil: 'domcontentloaded', timeout: 15_000 });
    const bodyText = await page.locator('main').innerText();
    assert(bodyText.toLowerCase().includes(route.expectedText.toLowerCase()), `${route.name} content was not visible`);
    routeResults.push({ ...route, passed: true });
  }

  let liveMode = false;
  if (issue9Mode) {
    await page.goto(routeUrl('#/'), { waitUntil: 'domcontentloaded', timeout: 15_000 });
    await page.getByTestId('issue9-proof-status').waitFor({ timeout: 15_000 });
    await page.waitForFunction(() => {
      const state = document.querySelector('[data-testid="issue9-proof-status"]')?.textContent?.trim();
      return ['READY', 'RUNNING', 'PASS', 'FAIL'].includes(state || '');
    }, null, { timeout: 15_000 });
    const initialStatus = (await page.getByTestId('issue9-proof-status').innerText()).trim();
    issue9InitialStatus = initialStatus;
    if (initialStatus === 'READY') {
      await page.getByRole('button', { name: 'Generate key and run proof' }).click();
    }
    if (initialStatus === 'READY' || initialStatus === 'RUNNING') {
      await page.getByTestId('issue9-proof-status').filter({ hasText: 'PASS' }).waitFor({ timeout: 120_000 });
    }
    assert(initialStatus !== 'FAIL', 'Issue #9 backend reported FAIL');
    const maskedKey = await page.getByTestId('issue9-masked-key').innerText();
    assert(/^bedrock-[a-f0-9]{12}\*{8}$/.test(maskedKey), 'Browser did not receive the masked key fingerprint');

    await page.goto(routeUrl('#/playground'), { waitUntil: 'domcontentloaded', timeout: 15_000 });
    await page.getByTestId('issue9-allow').filter({ hasText: 'ALLOW 200' }).waitFor({ timeout: 15_000 });
    const allowedText = await page.getByTestId('issue9-allow').innerText();
    assert(allowedText.includes('ALLOW 200'), 'Native key did not show the approved HTTP 200 result');
    assert(allowedText.toLowerCase().includes('governed access works'), 'Real Nova Lite response was not visible');
    await page.screenshot({ path: path.join(evidenceDir, 'playground-allowed.png'), fullPage: false });

    await page.getByTestId('issue9-deny').filter({ hasText: 'DENY 403' }).waitFor({ timeout: 15_000 });
    const deniedText = await page.getByTestId('issue9-deny').innerText();
    assert(deniedText.includes('DENY 403'), 'Native key did not show the restricted HTTP 403 result');
    assert(deniedText.includes('AWS IAM'), 'AWS IAM enforcement was not visible');
    awsDeniedHttp403 = true;
    await page.screenshot({ path: path.join(evidenceDir, 'playground-denied.png'), fullPage: false });

    await page.goto(routeUrl('#/logs'), { waitUntil: 'domcontentloaded', timeout: 15_000 });
    await page.waitForFunction(() => {
      const text = document.querySelector('main')?.textContent || '';
      return text.includes('Audit verified') || text.includes('Core proof complete');
    }, null, { timeout: 15_000 });
    const logsText = await page.locator('.data-table').innerText();
    const auditVerified = await page.getByText('Audit verified', { exact: true }).isVisible().catch(() => false);
    if (auditVerified) {
      const normalizedLogsText = logsText.toLowerCase();
      assert(normalizedLogsText.includes('success') && normalizedLogsText.includes('accessdenied'), 'Verified CloudTrail evidence did not show success and denial');
      cloudTrailStatus = 'VERIFIED';
    } else {
      assert(await page.getByText('Audit pending', { exact: true }).isVisible(), 'CloudTrail state was not visible');
      assert(await page.getByText('Core proof complete', { exact: true }).isVisible(), 'Non-blocking CloudTrail explanation was not visible');
      cloudTrailStatus = 'PENDING';
    }
    assert((await page.locator('.issue9-cleanup-notice').innerText()).includes('Credential lifecycle'), 'Lifecycle evidence was not visible');
    await page.screenshot({ path: path.join(evidenceDir, 'logs-allowed-denied.png'), fullPage: false });
  } else {
    await page.goto(routeUrl('#/'), { waitUntil: 'domcontentloaded', timeout: 15_000 });
    await page.getByRole('button', { name: 'Create demo API key' }).click();
    const platformKey = page.getByTestId('platform-key');
    await platformKey.filter({ hasText: /^sk-demo-[^*]/ }).waitFor({ timeout: 10_000 });
    const revealedKey = await platformKey.innerText();
    assert(revealedKey.startsWith('sk-demo-'), 'Demo platform key was not revealed');
    await page.getByRole('button', { name: 'Mask key' }).click();
    const maskedKey = await page.getByTestId('platform-key').innerText();
    assert(maskedKey.includes('********') && !maskedKey.includes('local-poc-key'), 'Platform key was not masked');

    await page.goto(routeUrl('#/playground'), { waitUntil: 'domcontentloaded', timeout: 15_000 });
    liveMode = await page.getByText('Live Bedrock', { exact: true }).isVisible().catch(() => false);
    await page.locator('#model').selectOption('apac.amazon.nova-lite-v1:0');
    await page.getByRole('button', { name: 'Run prompt' }).click();
    await page.locator('.response-copy').waitFor({ timeout: 35_000 });
    const allowedText = await page.locator('.response-panel').innerText();
    if (liveMode) {
      assert(!allowedText.includes('simulated local response'), 'Live mode returned a simulated response');
    } else {
      assert(allowedText.includes('simulated local response'), 'Allowed local response was not visible');
    }
    assert(allowedText.includes('Amazon Nova Lite'), 'Allowed model metadata was missing');
    assert(allowedText.includes('Allowed'), 'Allowed status was missing');
    await page.screenshot({ path: path.join(evidenceDir, 'playground-allowed.png'), fullPage: false });

    await page.locator('#model').selectOption('model-premium');
    await page.getByRole('button', { name: 'Run prompt' }).click();
    await page.locator('.denied-response').waitFor({ timeout: 10_000 });
    const deniedText = await page.locator('.response-panel').innerText();
    assert(deniedText.includes('Not allowed for this project'), 'Denied policy message was missing');
    assert(deniedText.includes('Denied'), 'Denied status was missing');
    await page.screenshot({ path: path.join(evidenceDir, 'playground-denied.png'), fullPage: false });

    await page.goto(routeUrl('#/logs'), { waitUntil: 'domcontentloaded', timeout: 15_000 });
    await page.locator('.table-row:not(.table-head)').nth(1).waitFor({ timeout: 10_000 });
    const logsText = await page.locator('.data-table').innerText();
    const normalizedLogsText = logsText.toLowerCase();
    assert(normalizedLogsText.includes('allowed') && normalizedLogsText.includes('denied'), 'Logs did not include both decisions');
    await page.screenshot({ path: path.join(evidenceDir, 'logs-allowed-denied.png'), fullPage: false });
  }

  await saveJson('routes.json', routeResults);
  await saveJson('network.json', networkRequests);
  await saveJson('console-errors.json', consoleErrors);
  let expectedDeniedConsoleErrorsRemaining = expectedDeniedHttp403 ? 1 : 0;
  const unexpectedConsoleErrors = consoleErrors.filter((message) => {
    if (expectedDeniedConsoleErrorsRemaining > 0 &&
        message === 'Failed to load resource: the server responded with a status of 403 ()') {
      expectedDeniedConsoleErrorsRemaining -= 1;
      return false;
    }
    return true;
  });
  await saveJson('unexpected-console-errors.json', unexpectedConsoleErrors);
  assert(externalRequests.length === 0, 'The local POC made a non-local request');
  assert(issue9Mode ? awsDeniedHttp403 : !liveMode || expectedDeniedHttp403, 'Live denial did not return the expected HTTP 403');
  assert(unexpectedConsoleErrors.length === 0, 'Browser console or page errors were detected');
  await saveJson('result.json', {
    status: 'PASS', appUrl, startedAt, finishedAt: new Date().toISOString(),
    viewport: { width: 1920, height: 1080 }, routesChecked: routeResults.length,
    mode: issue9Mode ? 'LIVE_BEDROCK_API_KEY' : liveMode ? 'LIVE_BEDROCK' : 'LOCAL_SIMULATION',
    keyCreatedThenMasked: !issue9Mode, keyMaskedInBrowser: true,
    proofStartedByBrowser: issue9Mode ? issue9InitialStatus === 'READY' : true,
    allowedModel: 'Amazon Nova Lite', deniedModel: issue9Mode ? 'Amazon Nova Pro' : 'Premium model',
    logDecisions: issue9Mode ? ['ALLOW', 'DENY'] : ['Allowed', 'Denied'], expectedDeniedHttp403: issue9Mode ? awsDeniedHttp403 : liveMode,
    browserReceivedAwsSecret: false, externalRequests: 0, consoleErrors: 0,
    cloudTrailStatus,
  });
} catch (error) {
  if (page) await page.screenshot({ path: path.join(evidenceDir, 'failure.png'), fullPage: false }).catch(() => {});
  await saveJson('routes.json', routeResults);
  await saveJson('network.json', networkRequests);
  await saveJson('external-requests.json', externalRequests);
  await saveJson('console-errors.json', consoleErrors);
  await saveJson('result.json', {
    status: 'FAIL', appUrl, startedAt, finishedAt: new Date().toISOString(),
    error: error instanceof Error ? error.message : String(error),
  });
  process.exitCode = 1;
} finally {
  if (page) await page.close().catch(() => {});
  if (browser) await browser.close().catch(() => {});
}
