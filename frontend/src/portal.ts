export type RouteId = 'home' | 'playground' | 'logs';

export interface PortalRoute {
  id: RouteId;
  label: string;
  path: string;
  icon: string;
}

export interface ModelEntry {
  id: string;
  name: string;
  access: 'Allowed' | 'Not allowed';
}

export interface PlatformResult {
  response?: string;
  message?: string;
  modelId: string;
  model: string;
  latencyMs: number;
  inputTokens: number;
  outputTokens: number;
  requestId: string;
  status: 'Allowed' | 'Denied' | 'Error';
}

export interface PlatformLog {
  timestamp: string;
  project: string;
  modelId: string;
  status: 'Allowed' | 'Denied' | 'Error';
  requestId: string;
  latencyMs: number;
  inputTokens: number;
  outputTokens: number;
}

export const PROJECT_ID = 'demo-security-app';
export const ALLOWED_MODEL_ID = 'apac.amazon.nova-lite-v1:0';
export const DENIED_MODEL_ID = 'model-premium';

export const routes: PortalRoute[] = [
  { id: 'home', label: 'Project', path: '#/', icon: 'P' },
  { id: 'playground', label: 'Playground', path: '#/playground', icon: '>' },
  { id: 'logs', label: 'Logs', path: '#/logs', icon: 'L' },
];

export const models: ModelEntry[] = [
  { id: ALLOWED_MODEL_ID, name: 'Amazon Nova Lite', access: 'Allowed' },
  { id: DENIED_MODEL_ID, name: 'Premium model', access: 'Not allowed' },
];

export function routeFromHash(hash: string): RouteId {
  const path = hash.replace(/^#/, '') || '/';
  return routes.find((route) => route.path.replace(/^#/, '') === path)?.id ?? 'home';
}
