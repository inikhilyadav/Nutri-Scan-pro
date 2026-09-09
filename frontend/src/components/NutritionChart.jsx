import React from 'react';

const BENCHMARKS = {
  Sugar: { max: 50, highRisk: 15, unit: 'g' },
  Fat: { max: 60, highRisk: 20, unit: 'g' },
  Protein: { max: 40, highRisk: 10, unit: 'g' },
  Fiber: { max: 20, highRisk: 5, unit: 'g' },
  Salt: { max: 5, highRisk: 1.5, unit: 'g' },
};

export default function NutritionChart({ nutrients }) {
  if (!nutrients || Object.keys(nutrients).length === 0) {
    return (
      <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
        No nutritional breakdown reported by the manufacturer.
      </div>
    );
  }

  return (
    <div className="nutrient-list">
      {Object.entries(nutrients).map(([name, val]) => {
        const numVal = Number(val) || 0;
        const bench = BENCHMARKS[name] || { max: 50, highRisk: 15, unit: 'g' };
        const percent = Math.min(100, Math.max(4, (numVal / bench.max) * 100));

        let barColor = 'var(--primary)';
        if (name === 'Sugar' && numVal > 15) barColor = 'var(--accent-rose)';
        else if (name === 'Sugar' && numVal > 8) barColor = 'var(--accent-amber)';
        else if (name === 'Fat' && numVal > 20) barColor = 'var(--accent-amber)';
        else if (name === 'Salt' && numVal > 1.5) barColor = 'var(--accent-rose)';
        else if (name === 'Protein' || name === 'Fiber') barColor = 'var(--accent-blue)';

        return (
          <div key={name} className="nutrient-row">
            <div className="nutrient-header">
              <span style={{ color: 'var(--text-secondary)' }}>{name}</span>
              <span className="nutrient-val">
                {numVal.toFixed(1)} {bench.unit} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/ 100g</span>
              </span>
            </div>
            <div className="nutrient-bar-track">
              <div
                className="nutrient-bar-fill"
                style={{ width: `${percent}%`, backgroundColor: barColor }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
