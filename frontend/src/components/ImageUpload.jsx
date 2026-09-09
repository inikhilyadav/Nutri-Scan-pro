import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { scanImage } from '../services/api';

export default function ImageUpload({ onBarcodeDetected }) {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [resultMsg, setResultMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setResultMsg({ type: 'error', text: 'Please upload an image file (PNG, JPG, or WEBP).' });
      return;
    }

    setPreview(URL.createObjectURL(file));
    setScanning(true);
    setResultMsg(null);

    try {
      const res = await scanImage(file);
      if (res.success && res.barcode) {
        setResultMsg({
          type: 'success',
          text: `Barcode detected: ${res.barcode}${res.is_valid_checksum ? ' (Valid check digit)' : ''}`,
        });
        onBarcodeDetected(res.barcode);
      } else {
        setResultMsg({
          type: 'warning',
          text: res.message || 'No barcode detected. Ensure the photo is clear and centered.',
        });
      }
    } catch (err) {
      setResultMsg({ type: 'error', text: err.message });
    } finally {
      setScanning(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div>
      <div
        className={`dropzone ${dragActive ? 'drag-active' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png, image/jpeg, image/webp"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />

        <div className="dropzone-icon">
          {scanning ? <Loader2 size={26} className="animate-spin" /> : <UploadCloud size={26} />}
        </div>

        <div>
          <strong style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>
            {scanning ? 'Analyzing photo for barcodes...' : 'Click to browse or drag & drop packaging photo'}
          </strong>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Supports high-resolution PNG, JPG, or WEBP images
          </p>
        </div>
      </div>

      {preview && (
        <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <img
            src={preview}
            alt="Upload preview"
            style={{
              width: '70px',
              height: '70px',
              objectFit: 'cover',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          />
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Selected Photo</span>
            {resultMsg && (
              <div
                className={`alert alert-${resultMsg.type === 'error' ? 'danger' : resultMsg.type}`}
                style={{ marginTop: '6px', padding: '8px 12px' }}
              >
                {resultMsg.type === 'success' ? (
                  <CheckCircle size={16} />
                ) : (
                  <AlertTriangle size={16} />
                )}
                <span>{resultMsg.text}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
