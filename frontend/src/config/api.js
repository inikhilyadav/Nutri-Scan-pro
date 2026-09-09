/**
 * Centralized API configuration.
 * Reads backend URL from VITE_API_URL environment variable.
 * Reads backend URL from VITE_API_URL environment variable.
 * Defaults to http://127.0.0.1:8001 for local development.
 */
const rawApiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');

export const API_ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/health`,
  STATS: `${API_BASE_URL}/api/stats`,
  VALIDATE_BARCODE: (code) => `${API_BASE_URL}/api/validate-barcode?barcode=${encodeURIComponent(code)}`,
  ANALYZE: (barcode) => `${API_BASE_URL}/api/analyze/${encodeURIComponent(barcode)}`,
  SCAN_IMAGE: `${API_BASE_URL}/api/scan/image`,
  CONTRIBUTE: `${API_BASE_URL}/api/contribute`,
};
