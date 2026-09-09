import React from 'react';
import {
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Info,
  Layers,
  Sparkles,
  ShieldCheck,
  Tag,
  PackageX,
} from 'lucide-react';
import NutritionChart from './NutritionChart';

export default function ReportView({ report, onReset }) {
  if (!report) return null;

  const score = report.score ?? 0;
  let scoreColor = '#10b981'; // Emerald
  let recBg = 'rgba(16, 185, 129, 0.15)';
  let recColor = '#34d399';

  if (score < 60) {
    scoreColor = '#f43f5e'; // Rose
    recBg = 'rgba(244, 63, 94, 0.15)';
    recColor = '#fda4af';
  } else if (score < 80) {
    scoreColor = '#f59e0b'; // Amber
    recBg = 'rgba(245, 158, 11, 0.15)';
    recColor = '#fcd34d';
  }

  // Circular gauge calculations (radius = 45, circumference = 2 * PI * 45 ≈ 282.7)
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const nutriscoreGrade = (report.nutriscore || 'UNKNOWN').toUpperCase();
  const novaGroup = report.nova_group;

  return (
    <div className="report-container">
      {/* Top action bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Barcode: <strong style={{ color: 'var(--text-secondary)' }}>{report.barcode}</strong>
        </span>
        <button type="button" className="btn-secondary" onClick={onReset}>
          <RotateCcw size={15} /> Scan Another Product
        </button>
      </div>

      {/* Main Product Header Card */}
      <div className="report-header-card">
        {report.image_url ? (
          <img src={report.image_url} alt={report.name} className="product-thumb" />
        ) : (
          <div className="product-thumb" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <PackageX size={44} color="var(--text-muted)" />
          </div>
        )}

        <div className="product-info-col">
          <h2>{report.name || 'Unknown Product'}</h2>
          <div className="product-brand">{report.brand || 'Brand not reported'}</div>

          <div className="badges-row">
            {nutriscoreGrade && (
              <span className={`nutriscore-badge nutriscore-${nutriscoreGrade}`}>
                NutriScore {nutriscoreGrade}
              </span>
            )}

            <span className={`badge badge-source ${report.source === 'Open Food Facts' ? 'verified' : ''}`}>
              <ShieldCheck size={14} />
              {report.source === 'Open Food Facts' ? 'Verified Database' : 'Community Added'}
            </span>
          </div>
        </div>

        {/* Circular Health Score Gauge */}
        <div className="score-gauge-wrapper">
          <div className="gauge-circle">
            <svg className="gauge-svg" viewBox="0 0 110 110">
              <circle cx="55" cy="55" r={radius} className="gauge-bg" />
              <circle
                cx="55"
                cy="55"
                r={radius}
                className="gauge-fill"
                stroke={scoreColor}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
              />
            </svg>
            <div className="gauge-text">
              <span className="gauge-number" style={{ color: scoreColor }}>
                {score}
              </span>
              <span className="gauge-max">/ 100</span>
            </div>
          </div>

          <div
            className="recommendation-pill"
            style={{ backgroundColor: recBg, color: recColor }}
          >
            {report.recommendation}
          </div>
        </div>
      </div>

      {/* Grid: Nutrition & NOVA / Reasons */}
      <div className="report-grid">
        {/* Left Column: Nutrition Chart */}
        <div className="report-section-card">
          <h3 className="section-title">
            <Flame size={20} color="var(--primary)" /> Nutrition per 100g
          </h3>
          <NutritionChart nutrients={report.nutrients} />
        </div>

        {/* Right Column: Processing & Score Breakdown */}
        <div className="report-section-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* NOVA Classification */}
          <div>
            <h3 className="section-title">
              <Layers size={20} color="var(--accent-blue)" /> Processing Level (NOVA)
            </h3>
            <div className="nova-card">
              <div className={`nova-num nova-${novaGroup || 'unknown'}`}>
                {novaGroup || '?'}
              </div>
              <div>
                <div className="nova-title">
                  {novaGroup ? `NOVA Group ${novaGroup}` : 'Not Classified'}
                </div>
                <div className="nova-desc">
                  {report.nova_label || 'Processing level has not been categorized yet.'}
                </div>
              </div>
            </div>
          </div>

          {/* Scoring Factors / Reasons */}
          <div>
            <h3 className="section-title">
              <Sparkles size={20} color="var(--accent-amber)" /> Health Factors
            </h3>
            {report.reasons && report.reasons.length > 0 ? (
              <ul className="reasons-list">
                {report.reasons.map((reason, idx) => (
                  <li key={idx} className="reason-item">
                    {reason.toLowerCase().includes('good') || reason.toLowerCase().includes('high fiber') ? (
                      <CheckCircle2 size={16} color="var(--primary)" style={{ flexShrink: 0 }} />
                    ) : (
                      <AlertTriangle size={16} color="var(--accent-rose)" style={{ flexShrink: 0 }} />
                    )}
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                No significant health deductions found in this profile.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Allergens, Traces, & Additives Section */}
      <div className="report-section-card">
        <h3 className="section-title">
          <Info size={20} color="var(--accent-purple)" /> Ingredients & Safety Advisories
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {/* Allergens */}
          <div>
            <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Declared Allergens:
            </div>
            {report.allergens && report.allergens.length > 0 ? (
              <div className="alert alert-danger" style={{ marginTop: 0 }}>
                <AlertTriangle size={18} style={{ flexShrink: 0 }} />
                <div>
                  <strong>Contains:</strong> {report.allergens.join(', ')}
                </div>
              </div>
            ) : (
              <div className="alert alert-success" style={{ marginTop: 0 }}>
                <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
                <span>No declared allergens registered.</span>
              </div>
            )}

            {report.traces && report.traces.length > 0 && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                May contain traces of: {report.traces.join(', ')}
              </div>
            )}
          </div>

          {/* Additives */}
          <div>
            <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Food Additives ({report.additives?.length || 0}):
            </div>
            {report.additives && report.additives.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {report.additives.map((add, i) => (
                  <span
                    key={i}
                    style={{
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-subtle)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {add}
                  </span>
                ))}
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No additives reported for this product.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
