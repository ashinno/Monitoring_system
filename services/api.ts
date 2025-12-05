import axios from 'axios';

const API = axios.create({
    baseURL: 'http://localhost:8000',
});

API.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const getNetworkTraffic = () => API.get('/traffic');
export const getNetworkAnalysis = () => API.get('/traffic/analyze');
export const getSystemMetrics = () => API.get('/api/system-metrics');
export const getSystemMetricsHistory = () => API.get('/api/system-metrics/history');

export const chatWithAI = (message: string, context: any[]) => API.post('/chat', { message, context });

export const exportData = (format: string, compress: boolean, startDate?: string, endDate?: string) => 
    API.get(`/api/reports/export?format=${format}&compress=${compress}${startDate ? `&start_date=${startDate}` : ''}${endDate ? `&end_date=${endDate}` : ''}`, { responseType: 'blob' });

export const startSimulation = (config: any) => API.post('/simulation/start', config);
export const stopSimulation = () => API.post('/simulation/stop');
export const getSimulationStatus = () => API.get('/simulation/status');

export const getSimulationProfiles = () => API.get('/simulation/profiles');
export const createSimulationProfile = (profile: any) => API.post('/simulation/profiles', profile);
export const deleteSimulationProfile = (id: string) => API.delete(`/simulation/profiles/${id}`);

export default API;
