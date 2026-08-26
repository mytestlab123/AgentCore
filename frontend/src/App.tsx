import { useEffect, useState } from 'react';
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

  const content = route === 'playground'
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
        <div className="workspace-label">Issue #4 MVP</div>
        <nav aria-label="Primary navigation">
          {routes.map((item) => (
            <a className={route === item.id ? 'active' : ''} href={item.path} key={item.id}>
              <span className="nav-icon">{item.icon}</span>{item.label}
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="environment-card"><span className="pulse-dot" /><div><strong>{isLiveMode ? 'Live AWS demo' : 'Local POC'}</strong><small>{isLiveMode ? 'Amazon Bedrock enabled' : 'No AWS calls'}</small></div></div>
          <a href="https://github.com/mytestlab123/AgentCore/issues/4" target="_blank" rel="noreferrer">Issue #4 <span>-&gt;</span></a>
        </div>
      </aside>

      {sidebarOpen && <button className="sidebar-scrim" type="button" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}

      <div className="main-shell">
        <header className="topbar">
          <button className="menu-button" type="button" aria-label="Open navigation" onClick={() => setSidebarOpen(true)}>Menu</button>
          <div className="breadcrumb"><span>AgentCore AI Platform</span><strong>/</strong><span>{routes.find((item) => item.id === route)?.label}</span></div>
          <div className="topbar-actions"><span className="demo-pill">3-minute POC</span><div className="user-button"><span>D</span><div><strong>demo developer</strong><small>demo-security-app</small></div></div></div>
        </header>
        <main className="page-content">{content}</main>
        <footer className="page-footer"><span>Issue #4 internal AI platform POC</span><span>{isLiveMode ? 'Live Bedrock responses' : 'Clearly marked local simulation'}</span></footer>
      </div>
    </div>
  );
}

export default App;
