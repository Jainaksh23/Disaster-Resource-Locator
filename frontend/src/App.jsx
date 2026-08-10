import { Routes, Route, Link } from 'react-router-dom';

function Home() {
  return (
    <div>
      <h1>🚨 Disaster Resource Locator</h1>
      <p>AI-powered disaster management system</p>
      <nav>
        <ul>
          <li><Link to="/dashboard">Dashboard</Link></li>
          <li><Link to="/reports">Reports</Link></li>
          <li><Link to="/resources">Resources</Link></li>
          <li><Link to="/triage">Triage</Link></li>
        </ul>
      </nav>
    </div>
  );
}

function Placeholder({ name }) {
  return (
    <div>
      <h1>{name}</h1>
      <p>Coming soon…</p>
      <Link to="/">← Home</Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<Placeholder name="Dashboard" />} />
      <Route path="/reports" element={<Placeholder name="Reports" />} />
      <Route path="/resources" element={<Placeholder name="Resources" />} />
      <Route path="/triage" element={<Placeholder name="Triage" />} />
    </Routes>
  );
}
