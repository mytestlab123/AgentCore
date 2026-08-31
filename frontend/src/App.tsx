import { useEffect, useState } from 'react';
import { isIssue9Mode } from './issue9-api';
import { Issue9HomePage, Issue9LogsPage, Issue9PlaygroundPage } from './issue9-pages';
import { HomePage, LogsPage, PlaygroundPage } from './pages';
import { isLiveMode } from './platform-api';
import { routeFromHash, routes, RouteId } from './portal';
import './App.css';

function App() {
  const [route, setRoute] = useState<RouteId>(() => routeFromHash(window.location.hash));
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const onHashChange = () => {
      setRoute(routeFromHash(window.location.hash));
      setSidebarOpen(false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const content = isIssue9Mode
    ? route === 'playground'
      ? <Issue9PlaygroundPage />
      : route === 'logs'
        ? <Issue9LogsPage />
        : <Issue9HomePage />
    : route === 'playground'
      ? <PlaygroundPage />
      : route === 'logs'
        ? <LogsPage />
        : <HomePage />;

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <a className="brand" href="#/" aria-label="AgentCore AI Platform home">
          <span className="brand-mark">AC</span>
          <span><strong>AgentCore</strong><small>AI Platform</small></span>
        </a>
        <div className="workspace-label">{isIssue9Mode ? 'Issue #12 Codex key POC' : 'Issue #4 MVP'}</div>
        <nav aria-label="Primary navigation">
          {routes.map((item) => (
            <a className={route === item.id ? 'active' : ''} href={item.path} key={item.id}>
              <span className="nav-icon">{item.icon}</span>{item.label}
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="environment-card"><span className="pulse-dot" /><div><strong>{isIssue9Mode ? 'Live AWS key demo' : isLiveMode ? 'Live AWS demo' : 'Local POC'}</strong><small>{isIssue9Mode ? 'amit stays server-side' : isLiveMode ? 'Amazon Bedrock enabled' : 'No AWS calls'}</small></div></div>
          <a href={`https://github.com/mytestlab123/AgentCore/issues/${isIssue9Mode ? '12' : '4'}`} target="_blank" rel="noreferrer">Issue #{isIssue9Mode ? '12' : '4'} <span>-&gt;</span></a>
        </div>
      </aside>

      {sidebarOpen && <button className="sidebar-scrim" type="button" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}

      <div className="main-shell">
        <header className="topbar">
          <button className="menu-button" type="button" aria-label="Open navigation" onClick={() => setSidebarOpen(true)}>Menu</button>
          <div className="breadcrumb"><span>AgentCore AI Platform</span><strong>/</strong><span>{routes.find((item) => item.id === route)?.label}</span></div>
          <div className="topbar-actions"><span className="demo-pill">{isIssue9Mode ? 'Live native key' : '3-minute POC'}</span><div className="user-button"><span>{isIssue9Mode ? 'A' : 'D'}</span><div><strong>{isIssue9Mode ? 'AWS test operator' : 'demo developer'}</strong><small>{isIssue9Mode ? 'amit / server-side' : 'demo-security-app'}</small></div></div></div>
        </header>
        <main className="page-content">{content}</main>
        <footer className="page-footer"><span>{isIssue9Mode ? 'Issue #12 governed Bedrock key to Codex POC' : 'Issue #4 internal AI platform POC'}</span><span>{isIssue9Mode ? 'Real AWS proof / retained demo setup' : isLiveMode ? 'Live Bedrock responses' : 'Clearly marked local simulation'}</span></footer>
      </div>
    </div>
  );
}

export default App;
