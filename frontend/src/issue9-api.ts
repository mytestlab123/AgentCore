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
