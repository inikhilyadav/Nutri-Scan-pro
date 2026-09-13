import React from 'react';
import { HeartPulse } from 'lucide-react';

export default function Header({ apiHealth }) {
  const isOnline = apiHealth?.status === 'ok' || apiHealth?.status === 'healthy';
  const isChecked = apiHealth !== null;

  return (
    <header className="header">
      <div className="brand">
        <div className="brand-icon">
          <HeartPulse size={26} strokeWidth={2.4} />
        </div>
        <div>
          <h1 className="brand-title">
            NutriScan <span style={{ fontSize: '0.8rem', opacity: 0.7, fontWeight: 500 }}>PRO</span>
          </h1>
          <p className="brand-subtitle">Smart Food Health & Nutritional Risk Analyzer</p>
        </div>
      </div>

      <div className="header-meta">
        <div
          className="status-pill"
          title={apiHealth?.error || (isOnline ? 'FastAPI Backend Healthy' : 'Backend offline or suspended')}
        >
          <span className={`status-indicator ${isOnline ? 'online' : 'offline'}`} />
          {isOnline
            ? 'FastAPI Backend Connected'
            : isChecked
            ? 'Backend Offline / Suspended'
            : 'Connecting to API...'}
        </div>
      </div>
    </header>
  );
}
