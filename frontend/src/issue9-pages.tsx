import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AwsPlaygroundResult, compareModels, CompareResult, getIssue9Proof, getNovaKeys, Issue9ProofStatus, NovaKeysStatus, revealIssue9Key, revealNovaKey, runAwsPlayground, runPlatformTool, startIssue9Proof } from './issue9-api';

export const KEY_REVEAL_SECONDS = 15;
export const nextRevealSeconds = (seconds: number) => Math.max(0, seconds - 1);

function Badge({ children, tone = 'green' }: { children: React.ReactNode; tone?: 'green' | 'amber' | 'gray' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="page-header"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></header>;
}

function useProofStatus() {
  const [status, setStatus] = useState<Issue9ProofStatus | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const next = await getIssue9Proof();
        if (active) { setStatus(next); setError(''); }
      } catch (caught) {
        if (active) setError(caught instanceof Error ? caught.message : 'Could not reach the Issue #9 backend.');
      }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 1500);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  return { status, setStatus, error, setError };
}

const proofSteps = [
  ['keyCreated', 'Generate Bedrock API key', '30-day service-specific credential'],
  ['approvedModelAllowed', 'Invoke Nova Lite', 'Real Bedrock response must return HTTP 200'],
  ['restrictedModelDenied', 'Block Nova Pro', 'AWS IAM must return HTTP 403'],
  ['cleanupVerified', 'Apply lifecycle policy', 'Successful demo retained; failed runs deleted'],
  ['cloudTrailCaptured', 'Capture CloudTrail', 'Success and AccessDenied events'],
] as const;

export function Issue9HomePage() {
  const { status, setStatus, error, setError } = useProofStatus();
  const [revealedKey, setRevealedKey] = useState('');
  const [revealSeconds, setRevealSeconds] = useState(0);
  const [novaKeys, setNovaKeys] = useState<NovaKeysStatus | null>(null);
  const [visibleNova, setVisibleNova] = useState<{ name: 'nova2' | 'nova_pro'; key: string; seconds: number } | null>(null);
  const start = async () => {
    setError('');
    try { setStatus(await startIssue9Proof()); }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Could not start the live proof.'); }
  };
  const proofUnavailable = status?.state === 'RUNNING' || status?.state === 'PASS';
  useEffect(() => {
    if (!revealedKey || revealSeconds <= 0) return;
    const timer = window.setTimeout(() => {
      if (revealSeconds === 1) {
        setRevealedKey('');
        setRevealSeconds(0);
      } else {
        setRevealSeconds(nextRevealSeconds);
      }
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [revealedKey, revealSeconds]);
  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const next = await getNovaKeys();
        if (active) setNovaKeys(next);
      } catch { /* Main proof error handling remains separate. */ }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 1500);
    return () => { active = false; window.clearInterval(timer); };
  }, []);
  useEffect(() => {
    if (!visibleNova || visibleNova.seconds <= 0) return;
    const timer = window.setTimeout(() => {
      if (visibleNova.seconds === 1) setVisibleNova(null);
      else setVisibleNova({ ...visibleNova, seconds: nextRevealSeconds(visibleNova.seconds) });
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [visibleNova]);

  const reveal = async () => {
    setError('');
    setRevealedKey('');
    try {
      const result = await revealIssue9Key();
      setRevealedKey(result.key);
      setRevealSeconds(Math.min(result.expiresInSeconds, KEY_REVEAL_SECONDS));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not reveal the retained key.');
    }
  };
  const copy = async () => {
    if (!revealedKey) return;
    try { await navigator.clipboard.writeText(revealedKey); }
    catch { setError('Clipboard access failed. Select and copy the revealed key manually.'); }
  };
  const revealNova = async (name: 'nova2' | 'nova_pro') => {
    setError('');
    try {
      const result = await revealNovaKey(name);
      setVisibleNova({ name, key: result.key, seconds: Math.min(result.expiresInSeconds, KEY_REVEAL_SECONDS) });
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Could not reveal the Nova key.'); }
  };
  const copyNova = async () => {
    if (!visibleNova) return;
    try { await navigator.clipboard.writeText(visibleNova.key); }
    catch { setError('Clipboard access failed. Select and copy the revealed key manually.'); }
  };

  return (
    <div data-testid="issue9-proof">
      <section className="hero-card compact-hero issue9-hero">
        <div><div className="hero-kicker"><span className="pulse-dot" /> AWS-native credential</div><h1>Native Bedrock access.<br /><span>Generate once. Demo again.</span></h1><p>Create one model-restricted Bedrock key, prove Nova Lite ALLOW and Nova Pro IAM DENY, capture CloudTrail, then retain the low-cost setup for repeat demos.</p><div className="hero-actions"><button className="button button-primary" type="button" disabled={proofUnavailable} onClick={() => void start()}>{status?.state === 'RUNNING' ? 'Proof running...' : status?.state === 'PASS' ? 'Retained proof ready' : 'Generate key and run proof'}</button><a className="button button-secondary" href="#/playground">View model results</a></div></div>
        <div className="hero-flow"><div className="flow-node"><small>Local operator backend</small><strong>amit / ap-southeast-1</strong></div><span className="flow-arrow">-&gt;</span><div className="flow-node flow-node-accent"><small>Bedrock API key</small><strong>{status?.key.masked || 'Secret stays server-side'}</strong></div><span className="flow-arrow">-&gt;</span><div className="flow-node"><small>AWS policy</small><strong>Nova Lite ALLOW / Nova Pro DENY</strong></div></div>
      </section>

      <section className="issue9-results">
        {(['nova2', 'nova_pro'] as const).map((name) => {
          const item = novaKeys?.keys[name];
          const shown = visibleNova?.name === name ? visibleNova.key : item?.masked;
          return <article className="panel codex-key-card" key={name}>
            <div className="key-card-top"><div><p className="eyebrow">Retained developer credential</p><h2>{name === 'nova2' ? 'Nova 2 Lite key' : 'Nova Pro key'}</h2></div><Badge tone={item?.available ? 'green' : 'amber'}>{item?.available ? 'READY' : 'MISSING'}</Badge></div>
            <p className="card-copy">Model-scoped Bedrock bearer key. It remains server-side until explicit reveal and is never stored by the browser.</p>
            <code>{shown || 'bedrock-********'}</code>
            <div className="key-actions"><button className="button button-secondary compact" disabled={!item?.available || Boolean(visibleNova)} onClick={() => void revealNova(name)}>Reveal key</button><button className="button button-primary compact" disabled={visibleNova?.name !== name} onClick={() => void copyNova()}>Copy key</button><small>{visibleNova?.name === name ? `Masks in ${visibleNova.seconds}s` : item?.model}</small></div>
          </article>;
        })}
      </section>

      <section className="issue9-control-grid">
        <article className="panel key-card issue9-key-card">
          <div className="key-card-top"><div><p className="eyebrow">Live credential</p><h2>Bedrock API key</h2></div><Badge tone={status?.key.deleted ? 'gray' : status?.key.created ? 'green' : 'amber'}>{status?.key.deleted ? 'Deleted' : status?.key.created ? 'Retained' : 'Not created'}</Badge></div>
          <p className="card-copy">Masked by default. Explicit reveal keeps the key in page memory for 15 seconds only; never capture it in screenshots.</p>
          <code data-testid="issue9-masked-key">{revealedKey || status?.key.masked || 'bedrock-********'}</code>
          <div className="key-actions">
            <button className="button button-secondary compact" type="button" disabled={!status?.key.created || Boolean(revealedKey)} onClick={() => void reveal()}>Reveal key</button>
            <button className="button button-primary compact" type="button" disabled={!revealedKey} onClick={() => void copy()}>Copy for Codex</button>
            <small>{revealedKey ? `Masks in ${revealSeconds}s` : 'Secret is masked'}</small>
          </div>
          {revealedKey && <div className="notice compact-notice"><span>!</span><div><strong>Clipboard warning</strong><p>Your operating system may retain copied text after this page masks it.</p></div></div>}
          <dl><div><dt>AWS profile</dt><dd>amit (server-side)</dd></div><div><dt>Region</dt><dd>ap-southeast-1</dd></div></dl>
          <div className="notice compact-notice"><span>i</span><div><strong>Retained demo setup</strong><p>Successful resources use cleanup=review, TTL=30-09-26, and a 30-day key lifetime. Failed runs delete automatically.</p></div></div>
        </article>

        <article className="panel proof-progress-card">
          <div className="panel-heading"><div><p className="eyebrow">Proof status</p><h2 data-testid="issue9-proof-status">{status?.state || 'CONNECTING'}</h2></div><Badge tone={status?.state === 'PASS' ? 'green' : status?.state === 'FAIL' ? 'gray' : 'amber'}>{status?.phase || 'Connecting'}</Badge></div>
          {error && <div className="error-box">{error}</div>}
          {status?.error && <div className="error-box">{status.error}</div>}
          <ol className="steps issue9-steps">
            {proofSteps.map(([key, label, detail], index) => <li className={status?.steps[key] ? 'complete' : ''} key={key}><span>{status?.steps[key] ? 'OK' : index + 1}</span><div><strong>{label}</strong><small>{detail}</small></div></li>)}
          </ol>
        </article>
      </section>
    </div>
  );
}

export function Issue9PlaygroundPage() {
  const toolPrompts = {
    ec2: 'List all EC2 instance names in the Singapore Region. Return names only.',
    inspector: 'List the top 10 Amazon Inspector findings as a table. Show severity, CVE or vulnerability ID, title, affected resource type, exploit availability, and fix availability. Use only the provided findings.',
    ssm: 'Fixed policy check: deny SSM Parameter Store list/get access.',
  } as const;
  const [model, setModel] = useState<'nova2' | 'nova_pro' | 'platform_haiku' | 'platform_gemini'>('nova2');
  const [tool, setTool] = useState<'ec2' | 'inspector' | 'ssm'>('ec2');
  const [prompt, setPrompt] = useState<string>(toolPrompts.ec2);
  const [result, setResult] = useState<AwsPlaygroundResult | null>(null);
  const [mode, setMode] = useState<'single' | 'compare'>('single');
  const [comparePrompt, setComparePrompt] = useState('Explain why a public S3 bucket is a security risk and give three remediation steps.');
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState('');
  const [running, setRunning] = useState(false);
  useEffect(() => { setResult(null); setError(''); }, [model, tool, prompt]);
  useEffect(() => { setCompareResult(null); setError(''); }, [mode, comparePrompt]);
  const run = async () => {
    setRunning(true); setError(''); setResult(null);
    try {
      if (model === 'platform_haiku') setResult(await runPlatformTool('azure.claude-haiku-4-5', tool, prompt));
      else if (model === 'platform_gemini') setResult(await runPlatformTool('gemini-2.5-flash-lite', tool, prompt));
      else setResult(await runAwsPlayground(model, tool, prompt));
    }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Live AWS playground failed.'); }
    finally { setRunning(false); }
  };
  const compare = async () => {
    setRunning(true); setError(''); setCompareResult(null);
    try { setCompareResult(await compareModels(comparePrompt)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Model comparison failed.'); }
    finally { setRunning(false); }
  };
  return (
    <>
      <div className="page-header-row"><PageHeader eyebrow="Issue #15 multi-provider POC" title="Governed model playground" description={mode === 'single' ? 'Use approved Nova models with fixed read-only AWS tools and an explicit SSM deny.' : 'Send one public-safe text prompt to Nova 2 Lite and PlatformAI GPT-5.6 Luna.'} /><Badge tone={(result?.decision === 'ALLOW' || compareResult) ? 'green' : result?.decision === 'DENY' ? 'gray' : 'amber'}>{compareResult ? 'COMPARED' : result?.decision || 'READY'}</Badge></div>
      {error && <div className="error-box">{error}</div>}
      <div className="mode-toggle" aria-label="Playground mode"><button className={mode === 'single' ? 'active' : ''} onClick={() => setMode('single')}>Single</button><button className={mode === 'compare' ? 'active' : ''} onClick={() => setMode('compare')}>Compare</button></div>
      {mode === 'single' ? <section className="playground-grid">
        <article className="panel prompt-panel"><label>Model</label><select value={model} onChange={(event) => setModel(event.target.value as typeof model)}><option value="nova2">Nova 2 Lite</option><option value="nova_pro">Nova Pro</option><option value="platform_haiku">PlatformAI Claude Haiku 4.5</option><option value="platform_gemini">PlatformAI Gemini 2.5 Flash Lite</option></select><label>AWS tool</label><select value={tool} onChange={(event) => { const next = event.target.value as typeof tool; setTool(next); setPrompt(toolPrompts[next]); }}><option value="ec2">EC2 inventory</option><option value="inspector">Inspector findings</option><option value="ssm">SSM secret access - deny proof</option></select><label>Question</label><textarea rows={7} value={prompt} disabled={tool === 'ssm'} onChange={(event) => setPrompt(event.target.value)} /><div className="prompt-footer"><small>{model.startsWith('platform_') && tool !== 'ssm' ? 'External provider receives public-safe sanitized records only.' : tool === 'ssm' ? 'The model is not called and no secret metadata is returned.' : 'Fixed allowlist; no arbitrary AWS commands.'}</small><button className="button button-primary" disabled={running} onClick={() => void run()}>{running ? 'Running...' : tool === 'ssm' ? 'Prove AWS deny' : 'Run live proof'}</button></div></article>
        <article className="panel response-panel"><div className="response-heading"><div><p className="eyebrow">Live result</p><h2>{result ? (result.tool === 'ssm' ? 'AWS IAM policy boundary' : result.model.startsWith('global.amazon') || result.model.startsWith('apac.amazon') ? 'Nova summary' : 'PlatformAI summary') : 'Ready'}</h2></div>{result && <Badge tone={result.decision === 'ALLOW' ? 'green' : 'gray'}>{result.decision}</Badge>}</div>{result ? <><div className={result.decision === 'DENY' ? 'error-box denied-response' : 'response-copy'}>{result.decision === 'DENY' ? result.answer : <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.answer}</ReactMarkdown>}</div><div className="metadata-grid"><div><span>Model</span><strong>{result.model}</strong></div><div><span>Sanitized records</span><strong>{result.records.length}</strong></div><div><span>Tokens</span><strong>{result.inputTokens} in / {result.outputTokens} out</strong></div><div><span>Completion</span><strong>{result.stopReason === 'max_tokens' ? 'Truncated' : 'Complete'}</strong></div></div></> : <div className="empty-response"><span>&gt;_</span><strong>Select a model and AWS tool</strong><p>EC2 and Inspector return sanitized facts. SSM must return an AWS IAM deny with zero secret data.</p></div>}</article>
      </section> : <><article className="panel compare-prompt"><label>Public-safe comparison prompt</label><textarea rows={4} maxLength={500} value={comparePrompt} onChange={(event) => setComparePrompt(event.target.value)} /><div className="prompt-footer"><small>Text only. No AWS inventory or Inspector data is sent to PlatformAI.</small><button className="button button-primary" disabled={running || !comparePrompt.trim()} onClick={() => void compare()}>{running ? 'Comparing...' : 'Compare models'}</button></div></article><section className="compare-grid">{(['Amazon Bedrock', 'GovTech PlatformAI'] as const).map((provider) => { const lane = compareResult?.results.find((item) => item.provider === provider); const success = lane?.status === 'ALLOW'; return <article className="panel compare-card" key={provider}><div className="response-heading"><div><p className="eyebrow">{provider}</p><h2>{provider === 'Amazon Bedrock' ? 'Nova 2 Lite' : 'GPT-5.6 Luna'}</h2></div><Badge tone={success ? 'green' : lane ? 'gray' : 'amber'}>{lane?.status || 'READY'}</Badge></div>{lane ? <><div className={success ? 'response-copy' : 'error-box denied-response'}>{success ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{lane.answer}</ReactMarkdown> : lane.answer}</div><div className="compare-meta"><span>{lane.latencyMs} ms</span><span>{lane.inputTokens ?? '-'} in / {lane.outputTokens ?? '-'} out</span><span>{lane.completion}</span></div></> : <div className="empty-response"><span>&gt;_</span><strong>Waiting for comparison</strong><p>One prompt, one independently returned provider response.</p></div>}</article>; })}</section><div className="notice"><span>i</span><div><strong>Comparison, not benchmark</strong><p>One prompt does not prove that either model is objectively better.</p></div></div></>}
    </>
  );
}

export function Issue9LogsPage() {
  const { status, error } = useProofStatus();
  return (
    <>
      <PageHeader eyebrow="AWS-native audit" title="CloudTrail evidence" description="Sanitized Converse events are correlated with the browser results using request-ID hashes; no bearer token or account identifier is exposed." />
      {error && <div className="error-box">{error}</div>}
      <div className="toolbar"><div className="search-box">{status?.cloudTrail.length || 0} CloudTrail event{status?.cloudTrail.length === 1 ? '' : 's'}</div><Badge tone={status?.auditState === 'VERIFIED' ? 'green' : 'amber'}>{status?.auditState === 'VERIFIED' ? 'Audit verified' : 'Audit pending'}</Badge></div>
      <article className="panel table-panel"><div className="data-table request-table"><div className="table-row table-head"><span>Request proof</span><span>Time</span><span>Operation</span><span>Model</span><span>Bearer key</span><span>Status</span></div>{status?.cloudTrail.map((event) => <div className="table-row" key={`${event.requestIdSha256}-${event.errorCode || 'success'}`}><span className="mono">{event.requestIdSha256?.slice(0, 12)}</span><span>{new Date(event.eventTime).toLocaleTimeString()}</span><span>{event.eventName}</span><span>{event.modelId || 'Not emitted by AWS'}</span><span>{event.bearerToken === true ? 'Confirmed' : 'Not emitted'}</span><span><Badge tone={event.errorCode ? 'gray' : 'green'}>{event.errorCode || 'Success'}</Badge></span></div>)}{!status?.cloudTrail.length && <div className="empty-log">CloudTrail evidence appears after AWS event history catches up.</div>}</div></article>
      <div className="notice issue9-cleanup-notice"><span>{status?.steps.cleanupVerified ? 'OK' : 'i'}</span><div><strong>Credential lifecycle</strong><p>{status?.cleanup?.intentionallyRetained ? 'The restricted 30-day Bedrock credential is intentionally retained for repeat demos through TTL=30-09-26.' : status?.steps.cleanupVerified ? 'The credential and disposable IAM user are verified deleted.' : 'Lifecycle evidence appears when the proof completes.'}</p></div></div>
      {status?.state === 'PASS' && status.auditState === 'PENDING' && <div className="notice"><span>i</span><div><strong>Core proof complete</strong><p>HTTP 200 allow, HTTP 403 IAM deny, and credential lifecycle are proven. CloudTrail event history is still propagating and will appear here asynchronously.</p></div></div>}
    </>
  );
}
