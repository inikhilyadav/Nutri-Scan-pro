import { API_BASE_URL, API_ENDPOINTS } from '../config/api';

/**
 * Enhanced fetch wrapper with custom timeout and friendly error diagnostics.
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return res;
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(
        `Connection timed out after ${timeoutMs / 1000}s. The backend (${API_BASE_URL}) is taking too long to respond. It may be sleeping or suspended on Render.`
      );
    }
    if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
      throw new Error(
        `Failed to fetch from backend API (${API_BASE_URL}). The server appears to be suspended or offline. Please check that the Render service is active.`
      );
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Fetch health status from FastAPI backend
 */
export async function getHealthStatus() {
  try {
    const res = await fetchWithTimeout(API_ENDPOINTS.HEALTH, {}, 5000);
    if (!res.ok) throw new Error(`Health check failed (${res.status})`);
    return await res.json();
  } catch (err) {
    console.warn('API health check error:', err.message);
    return { status: 'offline', error: err.message };
  }
}

/**
 * Fetch stats (scan count, accuracy) from backend
 */
export async function getStats() {
  try {
    const res = await fetchWithTimeout(API_ENDPOINTS.STATS, {}, 5000);
    if (!res.ok) throw new Error(`Failed to load stats (${res.status})`);
    return await res.json();
  } catch (err) {
    console.warn('Could not fetch stats:', err.message);
    return null;
  }
}

/**
 * Validates barcode and returns GS1 check digit result
 */
export async function validateBarcode(barcode) {
  if (!barcode) return { barcode: '', normalized: '', is_valid_checksum: null };
  try {
    const res = await fetchWithTimeout(API_ENDPOINTS.VALIDATE_BARCODE(barcode), {}, 5000);
    if (!res.ok) throw new Error(`Barcode validation error (${res.status})`);
    return await res.json();
  } catch (err) {
    console.warn('Validation error:', err.message);
    return { barcode, normalized: barcode.replace(/\D/g, ''), is_valid_checksum: null };
  }
}

/**
 * Fetch nutritional and health analysis report for a barcode
 */
export async function analyzeProduct(barcode) {
  const cleanCode = barcode.trim();
  if (!cleanCode) throw new Error('Please provide a barcode to analyze.');

  const res = await fetchWithTimeout(API_ENDPOINTS.ANALYZE(cleanCode), {}, 10000);
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

  const res = await fetchWithTimeout(API_ENDPOINTS.SCAN_IMAGE, {
    method: 'POST',
    body: formData,
  }, 15000);

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
  const res = await fetchWithTimeout(API_ENDPOINTS.CONTRIBUTE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  }, 10000);

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to save product contribution (${res.status})`);
  }
  return await res.json();
}
