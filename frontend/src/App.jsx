import React, { useState, useEffect } from 'react';
import { Camera, Search, Upload, AlertCircle, Loader2 } from 'lucide-react';
import Header from './components/Header';
import StatsBar from './components/StatsBar';
import ManualSearch from './components/ManualSearch';
import ImageUpload from './components/ImageUpload';
import BarcodeScanner from './components/BarcodeScanner';
import ReportView from './components/ReportView';
import ContributeModal from './components/ContributeModal';
import { getHealthStatus, getStats, analyzeProduct } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'camera' | 'upload'
  const [currentCode, setCurrentCode] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [apiHealth, setApiHealth] = useState(null);
  const [stats, setStats] = useState(null);

  // Contribute modal state for unknown barcodes
  const [isContributeOpen, setIsContributeOpen] = useState(false);
  const [notFoundBarcode, setNotFoundBarcode] = useState('');

  // Initial load
  useEffect(() => {
    refreshMetadata();
  }, []);

  const refreshMetadata = async () => {
    const [health, statsData] = await Promise.all([getHealthStatus(), getStats()]);
    setApiHealth(health);
    setStats(statsData);
  };

  const handleAnalyze = async (barcode) => {
    if (!barcode) return;
    setLoading(true);
    setError(null);
    setCurrentCode(barcode);

    try {
      const data = await analyzeProduct(barcode);

      if (data.not_found) {
        setNotFoundBarcode(barcode);
        setIsContributeOpen(true);
        setReport(null);
      } else if (!data.success && data.error) {
        setError(data.error);
        setReport(null);
      } else {
        setReport(data);
        // Refresh scan count stats
        getStats().then((s) => s && setStats(s));
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze product barcode.');
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const handleBarcodeDetected = (code) => {
    setCurrentCode(code);
    setActiveTab('search');
    handleAnalyze(code);
  };

  const handleReset = () => {
    setReport(null);
    setCurrentCode('');
    setError(null);
  };

  return (
    <div className="app-container">
      <Header apiHealth={apiHealth} />
      <StatsBar stats={stats} />

      {!report ? (
        <section className="action-card">
          <div className="tabs-header">
            <button
              type="button"
              className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              <Search size={18} /> Manual Search
            </button>

            <button
              type="button"
              className={`tab-btn ${activeTab === 'camera' ? 'active' : ''}`}
              onClick={() => setActiveTab('camera')}
            >
              <Camera size={18} /> Live Camera
            </button>

            <button
              type="button"
              className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              <Upload size={18} /> Upload Photo
            </button>
          </div>

          <div style={{ padding: '8px 0' }}>
            {activeTab === 'search' && (
              <ManualSearch
                initialCode={currentCode}
                onAnalyze={handleAnalyze}
                loading={loading}
              />
            )}

            {activeTab === 'camera' && (
              <BarcodeScanner onBarcodeDetected={handleBarcodeDetected} />
            )}

            {activeTab === 'upload' && (
              <ImageUpload onBarcodeDetected={handleBarcodeDetected} />
            )}
          </div>

          {loading && (
            <div
              style={{
                marginTop: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                color: 'var(--primary)',
                fontWeight: 600,
              }}
            >
              <Loader2 size={22} className="animate-spin" />
              <span>Fetching nutritional data and calculating health score...</span>
            </div>
          )}

          {error && (
            <div className="alert alert-danger" style={{ marginTop: '20px' }}>
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <div>{error}</div>
            </div>
          )}
        </section>
      ) : (
        <ReportView report={report} onReset={handleReset} />
      )}

      {/* Community Contribution Modal */}
      <ContributeModal
        barcode={notFoundBarcode}
        isOpen={isContributeOpen}
        onClose={() => setIsContributeOpen(false)}
        onSuccess={(newReport) => {
          setReport(newReport);
          getStats().then((s) => s && setStats(s));
        }}
      />

      <footer className="footer">
        <p>
          Powered by Open Food Facts global database &middot; NutriScore &middot; NOVA classification system
        </p>
        <p style={{ marginTop: '6px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Production Ready: React Frontend + FastAPI Backend + Docker
        </p>
      </footer>
    </div>
  );
}
