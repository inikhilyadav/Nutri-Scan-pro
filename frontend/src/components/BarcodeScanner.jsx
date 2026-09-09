import React, { useState, useRef, useEffect } from 'react';
import { Camera, RefreshCw, ScanLine, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { scanImage } from '../services/api';

export default function BarcodeScanner({ onBarcodeDetected }) {
  const [isActive, setIsActive] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // Default to rear camera
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [detected, setDetected] = useState(null);

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);

  const startCamera = async () => {
    setError(null);
    setDetected(null);
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      const constraints = {
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsActive(true);
    } catch (err) {
      console.error('Camera access error:', err);
      setError(
        'Could not access camera. Please allow camera permissions in your browser or use image upload.'
      );
      setIsActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsActive(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const switchCamera = () => {
    setFacingMode((prev) => (prev === 'environment' ? 'user' : 'environment'));
    if (isActive) {
      setTimeout(() => startCamera(), 100);
    }
  };

  const captureAndScan = async () => {
    if (!videoRef.current || !isActive) return;
    setScanning(true);
    setError(null);

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current || document.createElement('canvas');
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert canvas to blob
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.9));
      const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });

      const res = await scanImage(file);
      if (res.success && res.barcode) {
        setDetected(res.barcode);
        onBarcodeDetected(res.barcode);
      } else {
        setError(res.message || 'No barcode detected in view. Hold steady and try again.');
      }
    } catch (err) {
      setError(err.message || 'Scanning failed.');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '14px' }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Position the product barcode within the guide frame and capture:
        </p>
      </div>

      {!isActive ? (
        <div style={{ textAlign: 'center', padding: '36px 20px' }}>
          <button type="button" className="btn-primary" onClick={startCamera}>
            <Camera size={20} />
            Start Live Camera
          </button>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            Works best on mobile devices with high-resolution cameras.
          </p>
        </div>
      ) : (
        <div>
          <div className="camera-wrapper">
            <video ref={videoRef} className="camera-video" playsInline muted />
            <div className="camera-overlay">
              <div className="camera-reticle">
                <div className="camera-laser" />
              </div>
            </div>
          </div>

          <div className="camera-controls">
            <button
              type="button"
              className="btn-primary"
              onClick={captureAndScan}
              disabled={scanning}
            >
              {scanning ? (
                <>
                  <Loader2 size={18} className="animate-spin" /> Scanning...
                </>
              ) : (
                <>
                  <ScanLine size={18} /> Capture & Scan Barcode
                </>
              )}
            </button>

            <button
              type="button"
              className="btn-secondary"
              onClick={switchCamera}
              title="Switch camera"
            >
              <RefreshCw size={16} /> Switch Camera
            </button>

            <button
              type="button"
              className="btn-secondary"
              onClick={stopCamera}
              style={{ color: 'var(--accent-rose)' }}
            >
              Stop
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert-warning" style={{ marginTop: '16px' }}>
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {detected && (
        <div className="alert alert-success" style={{ marginTop: '16px' }}>
          <CheckCircle size={18} style={{ flexShrink: 0 }} />
          <span>Detected Barcode: <strong>{detected}</strong></span>
        </div>
      )}
    </div>
  );
}
