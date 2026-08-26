import {
  ALLOWED_MODEL_ID,
  DENIED_MODEL_ID,
  PlatformLog,
  PlatformResult,
  PROJECT_ID,
} from './portal';

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const isLiveMode = Boolean(apiBaseUrl) && import.meta.env.VITE_LOCAL_DEV !== 'true';
const keyStorageName = 'agentcore-issue4-platform-key';
const logStorageName = 'agentcore-issue4-local-logs';

function readLocalLogs(): PlatformLog[] {
  try {
    return JSON.parse(sessionStorage.getItem(logStorageName) || '[]') as PlatformLog[];
  } catch {
    return [];
  }
}

function writeLocalLog(log: PlatformLog) {
  sessionStorage.setItem(logStorageName, JSON.stringify([log, ...readLocalLogs()].slice(0, 25)));
}

async function readJson(response: Response): Promise<Record<string, unknown>> {
  const body = await response.json() as Record<string, unknown>;
  if (!response.ok && response.status !== 403) {
    throw new Error(typeof body.message === 'string' ? body.message : `Platform API failed with HTTP ${response.status}`);
  }
  return body;
}

export function getPlatformKey(): string {
  return sessionStorage.getItem(keyStorageName) || '';
}

export function maskPlatformKey(key = getPlatformKey()): string {
  return key ? `${key.slice(0, 12)}********` : 'Not created';
}

export async function createDemoKey(): Promise<string> {
  if (!isLiveMode) {
    const key = 'sk-demo-local-poc-key';
    sessionStorage.setItem(keyStorageName, key);
    return key;
  }
  const body = await readJson(await fetch(`${apiBaseUrl}/key`, { method: 'POST' }));
  const key = String(body.apiKey || '');
  if (!key.startsWith('sk-demo-')) throw new Error('Platform API returned an invalid demo key.');
  sessionStorage.setItem(keyStorageName, key);
  return key;
}

export async function invokeModel(prompt: string, modelId: string): Promise<PlatformResult> {
  const key = getPlatformKey();
  if (!key) throw new Error('Create the demo platform key on the Project page first.');

  if (isLiveMode) {
    const body = await readJson(await fetch(`${apiBaseUrl}/invoke`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': key },
      body: JSON.stringify({ prompt, modelId }),
    }));
    return body as unknown as PlatformResult;
  }

  await new Promise((resolve) => window.setTimeout(resolve, 350));
  const denied = modelId === DENIED_MODEL_ID;
  const result: PlatformResult = {
    response: denied ? undefined : 'This is a simulated local response. A public S3 bucket can expose data to unintended users. Block public access, review bucket policies and ACLs, then verify access with least privilege.',
    message: denied ? 'Not allowed for this project' : undefined,
    modelId,
    model: denied ? 'Premium model' : 'Amazon Nova Lite',
    latencyMs: denied ? 0 : 438,
    inputTokens: denied ? 0 : Math.max(12, Math.ceil(prompt.length / 4)),
    outputTokens: denied ? 0 : 42,
    requestId: `req_demo_${Date.now().toString(36).toUpperCase()}`,
    status: denied ? 'Denied' : 'Allowed',
  };
  writeLocalLog({
    timestamp: new Date().toISOString(), project: PROJECT_ID, modelId,
    status: result.status, requestId: result.requestId, latencyMs: result.latencyMs,
    inputTokens: result.inputTokens, outputTokens: result.outputTokens,
  });
  return result;
}

export async function getLogs(): Promise<PlatformLog[]> {
  const key = getPlatformKey();
  if (!key) return [];
  if (!isLiveMode) return readLocalLogs();
  const body = await readJson(await fetch(`${apiBaseUrl}/logs`, {
    headers: { 'x-api-key': key },
  }));
  return (body.items || []) as PlatformLog[];
}

export function resetLocalDemo() {
  if (!isLiveMode) {
    sessionStorage.removeItem(keyStorageName);
    sessionStorage.removeItem(logStorageName);
  }
}

export { ALLOWED_MODEL_ID };
