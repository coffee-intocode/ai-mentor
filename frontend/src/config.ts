/**
 * Frontend configuration
 * Uses environment variables for flexible deployment across environments
 */

// Base URL for API requests
// In development: empty string uses Vite proxy
// In production: should be set to the full backend URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

// API endpoints
export const API_ENDPOINTS = {
  configure: `${API_BASE_URL}/api/configure`,
  chat: `${API_BASE_URL}/api/chat`,
} as const
