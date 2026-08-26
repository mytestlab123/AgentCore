import { FormEvent, useEffect, useState } from 'react';
import {
  createDemoKey,
  getLogs,
  getPlatformKey,
  invokeModel,
  isLiveMode,
  maskPlatformKey,
} from './platform-api';
import { models, PlatformLog, PlatformResult, PROJECT_ID } from './portal';

function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="page-header"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></header>;
}

function Badge({ children, tone = 'green' }: { children: React.ReactNode; tone?: 'green' | 'amber' | 'gray' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function HomePage() {
  const [platformKey, setPlatformKey] = useState(getPlatformKey());
  const [revealed, setRevealed] = useState(false);
  const [error, setError] = useState('');

  const createKey = async () => {
    setError('');
    try {
      setPlatformKey(await createDemoKey());
      setRevealed(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not create the demo key.');
    }
  };

  return (
    <>
      <section className="hero-card compact-hero">
        <div><div className="hero-kicker"><span className="pulse-dot" /> One seeded project</div><h1>Governed model access.<br /><span>One platform key.</span></h1><p>The application team receives a project-scoped platform credential. AWS model credentials stay behind the platform API.</p><div className="hero-actions"><a className="button button-primary" href="#/playground">Open playground</a><a className="button button-secondary" href="#/logs">View logs</a></div></div>
        <div className="hero-flow"><div className="flow-node"><small>Developer app</small><strong>sk-demo-********</strong></div><span className="flow-arrow">-&gt;</span><div className="flow-node flow-node-accent"><small>Platform API</small><strong>Key + model policy + audit</strong></div><span className="flow-arrow">-&gt;</span><div className="flow-node"><small>Amazon Bedrock</small><strong>Nova Lite</strong></div></div>
      </section>

      <section className="two-column-grid home-grid">
        <article className="panel key-card primary-key-card">
          <div className="key-card-top"><div><p className="eyebrow">Project credential</p><h2>{PROJECT_ID}</h2></div><Badge>{platformKey ? 'Active' : 'Not created'}</Badge></div>
          <p className="card-copy">This demo key authenticates to the internal platform API. It is not an AWS or model-provider credential.</p>
          <code data-testid="platform-key">{revealed ? platformKey : maskPlatformKey(platformKey)}</code>
          {error && <div className="error-box">{error}</div>}
          {!platformKey ? <button className="button button-primary" type="button" onClick={() => void createKey()}>Create demo API key</button> : <button className="button button-secondary" type="button" onClick={() => setRevealed((value) => !value)}>{revealed ? 'Mask key' : 'Reveal in this session'}</button>}
        </article>

        <article className="panel">
          <div className="panel-heading"><div><p className="eyebrow">Project policy</p><h2>Model catalogue</h2></div><Badge tone={isLiveMode ? 'green' : 'amber'}>{isLiveMode ? 'Live AWS' : 'Local mock'}</Badge></div>
          <div className="policy-list">
            {models.map((model) => <div className="policy-row" key={model.id}><div><strong>{model.name}</strong><small>{model.id}</small></div><Badge tone={model.access === 'Allowed' ? 'green' : 'gray'}>{model.access}</Badge></div>)}
          </div>
          <div className="notice compact-notice"><span>i</span><div><strong>Central policy boundary</strong><p>The denied catalogue entry is visible but cannot reach Bedrock.</p></div></div>
        </article>
      </section>
    </>
  );
}

export function PlaygroundPage() {
  const [prompt, setPrompt] = useState('Explain why a public S3 bucket is a security risk and recommend remediation.');
  const [modelId, setModelId] = useState(models[0].id);
  const [result, setResult] = useState<PlatformResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runPrompt = async (event: FormEvent) => {
    event.preventDefault();
    if (!prompt.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try {
      setResult(await invokeModel(prompt, modelId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The platform request failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header-row"><PageHeader eyebrow="Use case 1 + 2" title="Playground" description="Run one approved Bedrock model or prove that central policy denies another model." /><Badge tone={isLiveMode ? 'green' : 'amber'}>{isLiveMode ? 'Live Bedrock' : 'Local simulation'}</Badge></div>
      <section className="playground-grid">
        <form className="panel prompt-panel" onSubmit={runPrompt}>
          <label htmlFor="project">Project</label><select id="project" value={PROJECT_ID} disabled><option>{PROJECT_ID}</option></select>
          <label htmlFor="model">Model</label><select id="model" value={modelId} onChange={(event) => setModelId(event.target.value)}>{models.map((model) => <option value={model.id} key={model.id}>{model.name} - {model.access}</option>)}</select>
          <label htmlFor="prompt">Prompt</label><textarea id="prompt" rows={10} value={prompt} onChange={(event) => setPrompt(event.target.value)} />
          <div className="prompt-footer"><small>Uses the platform key; no provider credential is exposed.</small><button className="button button-primary" type="submit" disabled={loading || !prompt.trim()}>{loading ? 'Running...' : 'Run prompt'}</button></div>
        </form>
        <article className="panel response-panel" aria-live="polite">
          <div className="response-heading"><div><p className="eyebrow">Platform result</p><h2>Response</h2></div>{result && <Badge tone={result.status === 'Allowed' ? 'green' : result.status === 'Denied' ? 'gray' : 'amber'}>{result.status}</Badge>}</div>
          {error && <div className="error-box">{error}</div>}
          {!result && !error ? <div className="empty-response"><span>&gt;_</span><strong>Ready for a request</strong><p>Create the project key, then run the approved or denied model.</p></div> : null}
          {result ? <><div className={result.status === 'Denied' ? 'error-box denied-response' : 'response-copy'}>{result.response || result.message}</div><div className="metadata-grid"><div><span>Model</span><strong>{result.model}</strong></div><div><span>Latency</span><strong>{result.latencyMs} ms</strong></div><div><span>Tokens</span><strong>{result.inputTokens} in / {result.outputTokens} out</strong></div><div><span>Request ID</span><strong className="mono">{result.requestId}</strong></div><div><span>Status</span><strong>{result.status}</strong></div><div><span>Provider credential</span><strong>Not exposed</strong></div></div></> : null}
        </article>
      </section>
    </>
  );
}

export function LogsPage() {
  const [logs, setLogs] = useState<PlatformLog[]>([]);
  const [error, setError] = useState('');
  const loadLogs = async () => {
    try { setLogs(await getLogs()); setError(''); } catch (caught) { setError(caught instanceof Error ? caught.message : 'Could not load logs.'); }
  };
  useEffect(() => { void loadLogs(); }, []);

  return (
    <>
      <PageHeader eyebrow="Central audit" title="Logs" description="Allowed and denied requests are recorded behind the same internal platform interface." />
      <div className="toolbar"><div className="search-box">{logs.length} request record{logs.length === 1 ? '' : 's'}</div><button className="button button-secondary" type="button" onClick={() => void loadLogs()}>Refresh</button></div>
      {error && <div className="error-box">{error}</div>}
      <article className="panel table-panel"><div className="data-table request-table"><div className="table-row table-head"><span>Request ID</span><span>Time</span><span>Project</span><span>Model</span><span>Latency / tokens</span><span>Status</span></div>{logs.map((row) => <div className="table-row" key={row.requestId}><span className="mono">{row.requestId}</span><span>{new Date(row.timestamp).toLocaleTimeString()}</span><span>{row.project}</span><span>{row.modelId}</span><span>{row.latencyMs} ms / {row.inputTokens + row.outputTokens}</span><span><Badge tone={row.status === 'Allowed' ? 'green' : row.status === 'Denied' ? 'gray' : 'amber'}>{row.status}</Badge></span></div>)}{logs.length === 0 && <div className="empty-log">No requests yet. Run both Playground models.</div>}</div></article>
    </>
  );
}
