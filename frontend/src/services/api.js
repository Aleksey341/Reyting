import axios from 'axios';

/**
 * API Base URL from environment
 * Vite uses VITE_* prefix for environment variables
 * Falls back to /api for local development (same origin)
 */
const API_URL = import.meta.env.VITE_API_BASE || '/api';

console.log(`[API] Initialized with base URL: ${API_URL}`);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error(`[API Error] ${error.response.status} ${error.response.statusText}`, error.response.data);
    } else if (error.request) {
      console.error('[API Error] No response received', error.request);
    } else {
      console.error('[API Error]', error.message);
    }
    return Promise.reject(error);
  }
);

export const mapService = {
  getMapData: (period, version) => {
    const params = {};
    if (period) params.period = period;
    if (version) params.version = version;
    return api.get('/map', { params });
  },
  getMODetails: (moId, period, version) => {
    const params = {};
    if (period) params.period = period;
    if (version) params.version = version;
    return api.get(`/map/${moId}`, { params });
  },
};

export const ratingService = {
  getRating: (period, version, sort = 'score_total', page = 1, pageSize = 50) => {
    return api.get('/rating', {
      params: { period, version, sort, page, page_size: pageSize },
    });
  },
  compareMOs: (moIds, period) => {
    return api.get('/rating/comparison', {
      params: { mo_ids: moIds.join(','), period },
    });
  },
};

export const indicatorService = {
  getIndicators: (block, isPublic) => {
    const params = {};
    if (block) params.block = block;
    if (isPublic !== undefined) params.is_public = isPublic;
    return api.get('/indicators', { params });
  },
  getMOIndicators: (moId, periodId) => {
    const params = {};
    if (periodId) params.period_id = periodId;
    return api.get(`/indicators/${moId}`, { params });
  },
};

export const methodologyService = {
  getVersions: () => {
    return api.get('/methodology/versions');
  },
  getScales: (versionId) => {
    return api.get(`/methodology/${versionId}/scales`);
  },
};

export const uploadService = {
  uploadFile: (sourceId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/upload/${sourceId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getUploadStatus: (uploadId) => {
    return api.get(`/upload/uploads/${uploadId}`);
  },
};

export default api;
