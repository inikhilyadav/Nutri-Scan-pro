import React, { useState } from 'react';
import { X, PlusCircle, CheckCircle, Loader2 } from 'lucide-react';
import { contributeProduct } from '../services/api';

export default function ContributeModal({ barcode, isOpen, onClose, onSuccess }) {
  if (!isOpen) return null;

  const [name, setName] = useState('');
  const [brand, setBrand] = useState('');
  const [sugar, setSugar] = useState('0.0');
  const [fat, setFat] = useState('0.0');
  const [salt, setSalt] = useState('0.0');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Product name is required.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        barcode,
        name: name.trim(),
        brand: brand.trim() || 'Unknown Brand',
        sugar: parseFloat(sugar) || 0.0,
        fat: parseFloat(fat) || 0.0,
        salt: parseFloat(salt) || 0.0,
      };

      const report = await contributeProduct(payload);
      onSuccess(report);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit product data.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.25rem', color: 'var(--text-primary)' }}>
              Product Not Found Yet
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Barcode: <strong>{barcode}</strong>
            </p>
          </div>
          <button type="button" className="btn-secondary" onClick={onClose} style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Open Food Facts doesn't have this product yet. Add the basics from the package label
          to save it in our community cache so anyone scanning this barcode gets an instant score!
        </p>

        {error && (
          <div className="alert alert-danger" style={{ marginBottom: '14px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label className="form-label">Product Name *</label>
            <input
              type="text"
              className="text-input"
              placeholder="e.g. Organic Almond Milk"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="form-field">
            <label className="form-label">Brand</label>
            <input
              type="text"
              className="text-input"
              placeholder="e.g. Silk / Oatly"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
            />
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label className="form-label">Sugar (g/100g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                className="text-input"
                value={sugar}
                onChange={(e) => setSugar(e.target.value)}
              />
            </div>
            <div className="form-field">
              <label className="form-label">Fat (g/100g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                className="text-input"
                value={fat}
                onChange={(e) => setFat(e.target.value)}
              />
            </div>
            <div className="form-field">
              <label className="form-label">Salt (g/100g)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="text-input"
                value={salt}
                onChange={(e) => setSalt(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
            <button
              type="button"
              className="btn-secondary"
              style={{ flex: 1, justifyContent: 'center' }}
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{ flex: 2 }}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <PlusCircle size={18} /> Save & Calculate Score
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
