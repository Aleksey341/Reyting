import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
