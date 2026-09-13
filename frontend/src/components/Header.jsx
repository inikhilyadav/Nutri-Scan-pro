import React from 'react';
import { HeartPulse } from 'lucide-react';

export default function Header({ apiHealth }) {
  const isOnline = apiHealth?.status === 'ok' || apiHealth?.status === 'healthy';

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
        <div className="status-pill" title="NutriScan Engine Active">
          <span className={`status-indicator ${isOnline ? 'online' : 'offline'}`} />
          {isOnline ? 'NutriScan Engine Online' : 'Connecting...'}
        </div>
      </div>
    </header>
  );
}
