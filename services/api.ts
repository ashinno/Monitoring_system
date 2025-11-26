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

export default API;
