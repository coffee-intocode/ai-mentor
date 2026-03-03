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
  configure: `${API_BASE_URL}/api/v1/chat/configure`,
  chatStream: `${API_BASE_URL}/api/v1/chat/stream`,
  conversations: `${API_BASE_URL}/api/v1/conversations`,
  conversationMessages: (conversationId: number, includeSuperseded = false) =>
    `${API_BASE_URL}/api/v1/messages/conversation/${conversationId}${
      includeSuperseded ? '?include_superseded=true' : ''
    }`,
} as const
