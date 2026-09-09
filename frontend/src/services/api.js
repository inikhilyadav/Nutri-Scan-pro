import { API_ENDPOINTS } from '../config/api';

/**
 * Fetch health status from FastAPI backend
 */
export async function getHealthStatus() {
  try {
    const res = await fetch(API_ENDPOINTS.HEALTH);
    if (!res.ok) throw new Error(`Health check failed (${res.status})`);
    return await res.json();
  } catch (err) {
    console.error('API health check error:', err);
    return { status: 'offline', error: err.message };
  }
}

/**
 * Fetch stats (scan count, accuracy) from backend
 */
export async function getStats() {
  try {
    const res = await fetch(API_ENDPOINTS.STATS);
    if (!res.ok) throw new Error(`Failed to load stats (${res.status})`);
    return await res.json();
  } catch (err) {
    console.warn('Could not fetch stats:', err);
    return null;
  }
}

/**
 * Validates barcode and returns GS1 check digit result
 */
export async function validateBarcode(barcode) {
  if (!barcode) return { barcode: '', normalized: '', is_valid_checksum: null };
  try {
    const res = await fetch(API_ENDPOINTS.VALIDATE_BARCODE(barcode));
    if (!res.ok) throw new Error(`Barcode validation error (${res.status})`);
    return await res.json();
  } catch (err) {
    console.warn('Validation error:', err);
    return { barcode, normalized: barcode.replace(/\D/g, ''), is_valid_checksum: null };
  }
}

/**
 * Fetch nutritional and health analysis report for a barcode
 */
export async function analyzeProduct(barcode) {
  const cleanCode = barcode.trim();
  if (!cleanCode) throw new Error('Please provide a barcode to analyze.');

  const res = await fetch(API_ENDPOINTS.ANALYZE(cleanCode));
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Server error during analysis (${res.status})`);
  }
  return await res.json();
}

/**
 * Upload an image containing a barcode to extract barcode digits
 */
export async function scanImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(API_ENDPOINTS.SCAN_IMAGE, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to process image (${res.status})`);
  }
  return await res.json();
}

/**
 * Submit missing product information to community cache
 */
export async function contributeProduct(data) {
  const res = await fetch(API_ENDPOINTS.CONTRIBUTE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to save product contribution (${res.status})`);
  }
  return await res.json();
}
