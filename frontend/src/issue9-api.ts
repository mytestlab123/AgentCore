export const isIssue9Mode = import.meta.env.VITE_DEMO_VARIANT === 'issue9';
const issue9ApiBaseUrl = (import.meta.env.VITE_ISSUE9_API_BASE_URL || '').replace(/\/$/, '');

export interface Issue9Decision {
  decision: 'ALLOW' | 'DENY';
  model: string;
  httpStatus: number;
  inputTokens?: number;
  outputTokens?: number;
  response?: string;
  enforcedBy?: string;
  requestIdSha256: string;
}

export interface Issue9CloudTrailEvent {
  eventTime: string;
  eventSource: string;
  eventName: string;
  errorCode: string | null;
  modelId: string | null;
  bearerToken: boolean | null;
  actorType: string;
  requestIdSha256: string;
}

export interface Issue9ProofStatus {
  state: 'READY' | 'RUNNING' | 'PASS' | 'FAIL';
  phase: string;
  auditState: 'NOT_STARTED' | 'PENDING' | 'VERIFIED';
  runId?: string;
  profileAlias: 'amit';
  region: 'ap-southeast-1';
  key: {
    created: boolean;
    masked: string | null;
    type?: string;
    ageDays?: number;
    deleted: boolean;
  };
  steps: {
    keyCreated: boolean;
    approvedModelAllowed: boolean;
    restrictedModelDenied: boolean;
    cloudTrailCaptured: boolean;
    cleanupVerified: boolean;
  };
  allowed: Issue9Decision | null;
  denied: Issue9Decision | null;
  cloudTrail: Issue9CloudTrailEvent[];
  cleanup: {
    credentialDeleted: boolean;
    userDeleted: boolean;
    cleanupFailed: boolean;
    intentionallyRetained?: boolean;
  } | null;
  error: string | null;
}

async function request(path: string, init?: RequestInit): Promise<Issue9ProofStatus> {
  if (!issue9ApiBaseUrl) throw new Error('Issue #9 backend URL is not configured.');
  const response = await fetch(`${issue9ApiBaseUrl}${path}`, init);
  const body = await response.json() as Issue9ProofStatus & { message?: string };
  if (!response.ok) throw new Error(body.message || `Issue #9 backend failed with HTTP ${response.status}`);
  return body;
}

export interface RevealedKey {
  key: string;
  expiresInSeconds: number;
}

export interface CodexKeyStatus {
  state: 'READY' | 'RUNNING' | 'CREATED' | 'FAIL';
  model: string;
  masked: string | null;
  message: string;
}

export interface NovaKeyStatus {
  available: boolean;
  masked: string | null;
  model: string;
}

export interface NovaKeysStatus {
  keys: Record<'nova2' | 'nova_pro', NovaKeyStatus>;
  expiresInSeconds: number;
}

export interface AwsPlaygroundResult {
  decision: 'ALLOW' | 'DENY';
  tool: 'ec2' | 'inspector' | 'ssm';
  model: string;
  records: Record<string, string>[];
  answer: string;
  inputTokens: number;
  outputTokens: number;
}

async function liveRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (!issue9ApiBaseUrl) throw new Error('Live AWS backend URL is not configured.');
  const response = await fetch(`${issue9ApiBaseUrl}${path}`, init);
  const body = await response.json() as T & { message?: string };
  if (!response.ok) throw new Error(body.message || `Live AWS action failed with HTTP ${response.status}`);
  return body;
}

export function getNovaKeys(): Promise<NovaKeysStatus> {
  return liveRequest('/nova-keys');
}

export function revealNovaKey(name: 'nova2' | 'nova_pro'): Promise<RevealedKey> {
  return liveRequest(`/nova-keys/${name}/reveal`, { method: 'POST', cache: 'no-store' });
}

export function runAwsPlayground(model: 'nova2' | 'nova_pro', tool: 'ec2' | 'inspector' | 'ssm', prompt: string): Promise<AwsPlaygroundResult> {
  return liveRequest('/aws-playground', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model, tool, prompt }),
  });
}

async function codexKeyRequest(path: string, init?: RequestInit): Promise<CodexKeyStatus> {
  if (!issue9ApiBaseUrl) throw new Error('Issue #12 backend URL is not configured.');
  const response = await fetch(`${issue9ApiBaseUrl}${path}`, init);
  const body = await response.json() as CodexKeyStatus & { message: string };
  if (!response.ok) throw new Error(body.message || `Codex key action failed with HTTP ${response.status}`);
  return body;
}

export function getCodexKey(): Promise<CodexKeyStatus> {
  return codexKeyRequest('/codex-key');
}

export function createCodexKey(model: string): Promise<CodexKeyStatus> {
  return codexKeyRequest('/codex-key', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model }),
  });
}

export async function revealCodexKey(): Promise<RevealedKey> {
  if (!issue9ApiBaseUrl) throw new Error('Issue #12 backend URL is not configured.');
  const response = await fetch(`${issue9ApiBaseUrl}/codex-key/reveal`, { method: 'POST', cache: 'no-store' });
  const body = await response.json() as RevealedKey & { message?: string };
  if (!response.ok) throw new Error(body.message || `Codex key reveal failed with HTTP ${response.status}`);
  return body;
}

export async function revealIssue9Key(): Promise<RevealedKey> {
  if (!issue9ApiBaseUrl) throw new Error('Issue #9 backend URL is not configured.');
  const response = await fetch(`${issue9ApiBaseUrl}/key/reveal`, { method: 'POST', cache: 'no-store' });
  const body = await response.json() as RevealedKey & { message?: string };
  if (!response.ok) throw new Error(body.message || `Key reveal failed with HTTP ${response.status}`);
  return body;
}

export function getIssue9Proof(): Promise<Issue9ProofStatus> {
  return request('/proof');
}

export function startIssue9Proof(): Promise<Issue9ProofStatus> {
  return request('/proof', { method: 'POST' });
}
