/**
 * API client for backend communication.
 */

import axios from 'axios';
import type { DrugQuery, DrugAnalysisResult, AutocompleteOption } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minute timeout for comprehensive analysis (50+ studies + 10-15 Gemini calls)
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  /**
   * Get drug autocomplete suggestions.
   */
  async autocomplete(query: string, limit: number = 10): Promise<AutocompleteOption[]> {
    const response = await api.post<AutocompleteOption[]>('/api/autocomplete', {
      query,
      limit,
    });
    return response.data;
  },

  /**
   * Analyze a drug for non-response (traditional endpoint).
   */
  async analyzeDrug(query: DrugQuery): Promise<DrugAnalysisResult> {
    const response = await api.post<DrugAnalysisResult>('/api/analyze', query);
    return response.data;
  },

  /**
   * Get SSE URL for real-time progress updates.
   * Use this with the useSSE hook for live progress display.
   */
  getAnalyzeStreamURL(query: DrugQuery): string {
    const params = new URLSearchParams();
    params.append('drug', query.drug);
    if (query.indication) {
      params.append('indication', query.indication);
    }
    if (query.population) {
      params.append('population', query.population);
    }

    // For POST with SSE, we need to serialize the body as JSON
    // EventSource only supports GET, so we'll encode data in the body via fetch
    // Actually, let's use a simpler approach - just return the endpoint
    // and the consuming code will handle the POST

    return `${API_BASE_URL}/api/analyze-stream`;
  },

  /**
   * Create SSE connection for drug analysis with progress updates.
   * This returns the POST body for the SSE endpoint.
   */
  getAnalyzeStreamBody(query: DrugQuery): string {
    return JSON.stringify(query);
  },

  /**
   * Health check.
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/api/health');
    return response.data;
  },
};
