import React, { useState, useEffect } from 'react';
import { Search, AlertCircle, CheckCircle2 } from 'lucide-react';
import { validateBarcode } from '../services/api';

const SAMPLES = [
  { name: 'Nutella', code: '3017620422003' },
  { name: 'Coca-Cola', code: '5449000000996' },
  { name: 'Barilla Pasta', code: '8076800195057' },
];

export default function ManualSearch({ onAnalyze, loading, initialCode = '' }) {
  const [code, setCode] = useState(initialCode);
  const [checksumValid, setChecksumValid] = useState(null);

  useEffect(() => {
    if (initialCode) {
      setCode(initialCode);
      checkValidation(initialCode);
    }
  }, [initialCode]);

  const checkValidation = (val) => {
    let clean = (val || '').replace(/\D/g, '');
    if (clean.length === 12) {
      clean = '0' + clean; // UPC-A padded to 13-digit EAN
    }
    if (clean.length === 13) {
      const digits = clean.split('').map(Number);
      const total = digits.slice(0, 12).reduce((sum, d, i) => sum + d * (i % 2 === 0 ? 1 : 3), 0);
      const checkDigit = (10 - (total % 10)) % 10;
      setChecksumValid(checkDigit === digits[12]);
    } else {
      setChecksumValid(null);
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setCode(val);
    checkValidation(val);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const clean = code.trim();
    if (clean) {
      onAnalyze(clean);
    }
  };

  return (
    <div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '8px' }}>
        Enter any standard 8, 12, or 13-digit retail barcode (EAN / UPC):
      </p>

      <form onSubmit={handleSubmit} className="input-group">
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            type="text"
            className="text-input"
            style={{ width: '100%' }}
            placeholder="e.g. 3017620422003"
            value={code}
            onChange={handleInputChange}
            disabled={loading}
          />
          {checksumValid === true && (
            <span
              style={{
                position: 'absolute',
                right: '14px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.78rem',
                fontWeight: 600,
              }}
            >
              <CheckCircle2 size={16} /> Valid EAN
            </span>
          )}
        </div>

        <button type="submit" className="btn-primary" disabled={loading || !code.trim()}>
          <Search size={18} />
          {loading ? 'Analyzing...' : 'Search & Analyze'}
        </button>
      </form>

      {checksumValid === false && (
        <div className="alert alert-warning">
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <div>
            <strong>Check digit mismatch:</strong> The last digit does not match the GS1 check formula.
            Double-check the digits on the package to prevent a false "not found" error.
          </div>
        </div>
      )}

      <div className="quick-samples">
        <span className="quick-sample-label">Try sample:</span>
        {SAMPLES.map((s) => (
          <button
            key={s.code}
            type="button"
            className="sample-chip"
            onClick={() => {
              setCode(s.code);
              checkValidation(s.code);
              onAnalyze(s.code);
            }}
          >
            {s.name} ({s.code})
          </button>
        ))}
      </div>
    </div>
  );
}
