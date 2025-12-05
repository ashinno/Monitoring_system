import React, { useEffect, useState } from 'react';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Cpu, HardDrive, Server, Clock, Activity } from 'lucide-react';
import { getSystemMetrics, getSystemMetricsHistory } from '../services/api';

interface SystemMetricsData {
    timestamp: string;
    cpu: {
        usagePercent: number;
    };
    memory: {
        total: number;
        available: number;
        percent: number;
        used: number;
    };
    disk: {
        total: number;
        free: number;
        percent: number;
        used: number;
    };
}

const SystemMetrics: React.FC = () => {
    const [metricsHistory, setMetricsHistory] = useState<SystemMetricsData[]>([]);
    const [currentMetrics, setCurrentMetrics] = useState<SystemMetricsData | null>(null);
    const [viewMode, setViewMode] = useState<'live' | 'history'>('live');

    const fetchMetrics = async () => {
        if (viewMode === 'history') return; // Don't poll in history mode

        try {
            const response = await getSystemMetrics();
            const data = response.data;
            setCurrentMetrics(data);
            setMetricsHistory(prev => {
                const updated = [...prev, data];
                // In live mode, keep last 60 points (1 minute) for smooth real-time view
                if (updated.length > 60) return updated.slice(-60);
                return updated;
            });
        } catch (error) {
            console.error("Failed to fetch system metrics", error);
        }
    };

    const fetchHistory = async () => {
        try {
            const response = await getSystemMetricsHistory();
            setMetricsHistory(response.data);
            // Set current metrics to the last one in history
            if (response.data.length > 0) {
                setCurrentMetrics(response.data[response.data.length - 1]);
            }
        } catch (error) {
            console.error("Failed to fetch history", error);
        }
    };

    useEffect(() => {
        if (viewMode === 'live') {
            fetchMetrics();
            const interval = setInterval(fetchMetrics, 1000); // 1s latency
            return () => clearInterval(interval);
        } else {
            fetchHistory();
        }
    }, [viewMode]);

    if (!currentMetrics) return <div className="text-slate-400">Loading System Metrics...</div>;

    const formatTime = (iso: string) => {
        const d = new Date(iso);
        return `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
    };

    const chartData = metricsHistory.map(m => ({
        time: formatTime(m.timestamp),
        cpu: m.cpu.usagePercent,
        memory: m.memory.percent,
        disk: m.disk.percent
    }));

    return (
        <div className="glass-panel p-6 rounded-xl mb-6">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Server className="text-emerald-400" />
                    System Resources
                </h3>
                <div className="flex bg-slate-800/50 rounded-lg p-1 border border-slate-700">
                    <button 
                        onClick={() => setViewMode('live')}
                        className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${viewMode === 'live' ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-400 hover:text-white'}`}
                    >
                        <div className="flex items-center gap-1">
                            <Activity size={12} />
                            Live
                        </div>
                    </button>
                    <button 
                        onClick={() => setViewMode('history')}
                        className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${viewMode === 'history' ? 'bg-blue-500/20 text-blue-400' : 'text-slate-400 hover:text-white'}`}
                    >
                        <div className="flex items-center gap-1">
                            <Clock size={12} />
                            24h History
                        </div>
                    </button>
                </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {/* CPU Card */}
                <div className={`p-4 rounded-lg border ${currentMetrics.cpu.usagePercent > 80 ? 'bg-red-500/10 border-red-500/50' : currentMetrics.cpu.usagePercent > 50 ? 'bg-yellow-500/10 border-yellow-500/50' : 'bg-slate-800/50 border-slate-700'}`}>
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-slate-400 text-xs font-mono">CPU Usage</span>
                        <Cpu className={`w-4 h-4 ${currentMetrics.cpu.usagePercent > 80 ? 'text-red-400' : 'text-emerald-400'}`} />
                    </div>
                    <div className="text-2xl font-bold text-white font-mono">
                        {currentMetrics.cpu.usagePercent.toFixed(1)}%
                    </div>
                    <div className="w-full bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden">
                        <div 
                            className={`h-full rounded-full transition-all duration-500 ${currentMetrics.cpu.usagePercent > 80 ? 'bg-red-500' : 'bg-emerald-500'}`}
                            style={{ width: `${currentMetrics.cpu.usagePercent}%` }}
                        />
                    </div>
                </div>

                {/* Memory Card */}
                <div className={`p-4 rounded-lg border ${currentMetrics.memory.percent > 90 ? 'bg-red-500/10 border-red-500/50' : 'bg-slate-800/50 border-slate-700'}`}>
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-slate-400 text-xs font-mono">Memory</span>
                        <Server className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="text-2xl font-bold text-white font-mono">
                        {currentMetrics.memory.percent.toFixed(1)}%
                    </div>
                    <div className="text-xs text-slate-500 mt-1 font-mono">
                        {(currentMetrics.memory.used / 1024 / 1024 / 1024).toFixed(1)} GB / {(currentMetrics.memory.total / 1024 / 1024 / 1024).toFixed(1)} GB
                    </div>
                </div>

                {/* Disk Card */}
                <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-slate-400 text-xs font-mono">Disk I/O</span>
                        <HardDrive className="w-4 h-4 text-purple-400" />
                    </div>
                    <div className="text-2xl font-bold text-white font-mono">
                        {currentMetrics.disk.percent.toFixed(1)}%
                    </div>
                    <div className="text-xs text-slate-500 mt-1 font-mono">
                        {(currentMetrics.disk.free / 1024 / 1024 / 1024).toFixed(1)} GB Free
                    </div>
                </div>
            </div>

            <div className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                        <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} domain={[0, 100]} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                            itemStyle={{ fontSize: '12px' }}
                            labelStyle={{ color: '#94a3b8', fontSize: '10px', marginBottom: '4px' }}
                        />
                        <Line type="monotone" dataKey="cpu" stroke="#10b981" strokeWidth={2} dot={false} name="CPU %" />
                        <Line type="monotone" dataKey="memory" stroke="#3b82f6" strokeWidth={2} dot={false} name="Mem %" />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default SystemMetrics;
