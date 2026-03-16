import axios from 'axios';

export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

const API = axios.create({
    baseURL: API_BASE_URL,
});

API.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

API.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn("Unauthorized access. Redirecting to login.");
            localStorage.removeItem('token');
            window.location.href = '/'; // Redirect to login/home
        }
        return Promise.reject(error);
    }
);

export const getNetworkTraffic = () => API.get('/traffic');
export const getNetworkAnalysis = () => API.get('/traffic/analyze');
export const getSystemMetrics = () => API.get('/api/system-metrics');
export const getSystemMetricsHistory = () => API.get('/api/system-metrics/history');

export const chatWithAI = (message: string, context: any[]) => API.post('/chat', { message, context });

export const exportData = (format: string, compress: boolean, startDate?: string, endDate?: string) => 
    API.get(`/api/reports/export?format=${format}&compress=${compress}${startDate ? `&start_date=${startDate}` : ''}${endDate ? `&end_date=${endDate}` : ''}`, { responseType: 'blob' });

export const startInterception = (config: any) => API.post('/interception/start', config);
export const stopInterception = () => API.post('/interception/stop');
export const getInterceptionStatus = () => API.get('/interception/status');
export const getInterceptionInterfaces = () => API.get('/interception/interfaces');

export const getSimulationProfiles = () => API.get('/simulation/profiles');
export const createSimulationProfile = (profile: any) => API.post('/simulation/profiles', profile);
export const deleteSimulationProfile = (id: string) => API.delete(`/simulation/profiles/${id}`);

export type AttackScenario = 'ddos' | 'port_scan' | 'brute_force' | 'data_exfiltration';

type AttackTrafficProfile = {
    destinationIp: string;
    port: number;
    protocol: 'TCP' | 'UDP';
    bytesMin: number;
    bytesMax: number;
    packetMin: number;
    packetMax: number;
    sourceIp: () => string;
};

const attackProfiles: Record<AttackScenario, AttackTrafficProfile> = {
    ddos: {
        destinationIp: '192.168.1.100',
        port: 443,
        protocol: 'TCP',
        bytesMin: 2000000,
        bytesMax: 8000000,
        packetMin: 300,
        packetMax: 1200,
        sourceIp: () => `${Math.floor(Math.random() * 220) + 11}.${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}`,
    },
    port_scan: {
        destinationIp: '192.168.1.100',
        port: 0,
        protocol: 'TCP',
        bytesMin: 200,
        bytesMax: 3000,
        packetMin: 1,
        packetMax: 8,
        sourceIp: () => '192.168.1.50',
    },
    brute_force: {
        destinationIp: '192.168.1.100',
        port: 22,
        protocol: 'TCP',
        bytesMin: 500,
        bytesMax: 4000,
        packetMin: 2,
        packetMax: 20,
        sourceIp: () => '192.168.1.50',
    },
    data_exfiltration: {
        destinationIp: '45.33.22.11',
        port: 443,
        protocol: 'TCP',
        bytesMin: 1000000,
        bytesMax: 9000000,
        packetMin: 50,
        packetMax: 400,
        sourceIp: () => '192.168.1.100',
    },
};

const randomInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;

export const simulateAttackBurst = async (scenario: AttackScenario, count: number = 24) => {
    const profile = attackProfiles[scenario];
    const requests = Array.from({ length: count }).map((_, idx) => {
        const port = scenario === 'port_scan' ? idx + 1 : profile.port;
        const payload = {
            id: `${scenario}-${Date.now()}-${idx}-${Math.random().toString(16).slice(2, 8)}`,
            timestamp: new Date().toISOString(),
            sourceIp: profile.sourceIp(),
            destinationIp: profile.destinationIp,
            port,
            protocol: profile.protocol,
            bytesTransferred: randomInt(profile.bytesMin, profile.bytesMax),
            packetCount: randomInt(profile.packetMin, profile.packetMax),
            latency: randomInt(1, 30),
            isAnomalous: true,
        };
        return API.post('/traffic', payload);
    });
    const settled = await Promise.allSettled(requests);
    const successful = settled.filter((entry) => entry.status === 'fulfilled').length;
    return { successful, attempted: count };
};

// Agent Management
export const getAgentStatus = () => API.get('/agent/status');
export const startAgent = () => API.post('/agent/start');
export const stopAgent = () => API.post('/agent/stop');

export const getKeylogStats = (startDate?: string, endDate?: string) => 
    API.get(`/logs/stats/keylogs${startDate ? `?start_date=${startDate}` : ''}${endDate ? `&end_date=${endDate}` : ''}`);

export default API;
