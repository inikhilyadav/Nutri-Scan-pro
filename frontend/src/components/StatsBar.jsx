import React from 'react';
import { BarChart3, Target, Database } from 'lucide-react';

export default function StatsBar({ stats }) {
  const count = stats?.scan_count ?? 0;
  const accuracy = stats?.ingredient_risk_accuracy;
  const isSupabase = stats?.storage_mode === 'supabase';

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-icon-wrapper emerald">
          <BarChart3 size={22} />
        </div>
        <div>
          <div className="stat-value">{count.toLocaleString()}+</div>
          <div className="stat-label">Products Analyzed</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon-wrapper purple">
          <Target size={22} />
        </div>
        <div>
          <div className="stat-value">
            {accuracy ? `${Math.round(accuracy.value * 100)}%` : 'Benchmark'}
          </div>
          <div className="stat-label">
            {accuracy ? `Verified on ${accuracy.n} products` : 'Ingredient-Risk Accuracy'}
          </div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon-wrapper">
          <Database size={22} />
        </div>
        <div>
          <div className="stat-value" style={{ fontSize: '1.1rem' }}>
            {isSupabase ? 'Cloud DB' : 'Local Fallback'}
          </div>
          <div className="stat-label">
            {isSupabase ? 'Supabase Synced' : 'Persistent Storage'}
          </div>
        </div>
      </div>
    </div>
  );
}
