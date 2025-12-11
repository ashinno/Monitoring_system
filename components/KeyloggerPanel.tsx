import React, { useEffect, useState } from 'react';
import { 
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
    LineChart, Line, CartesianGrid 
} from 'recharts';
import { Keyboard, Clock, Monitor, Hash, Download } from 'lucide-react';
import KeymapHeatmap from './KeymapHeatmap';
import { getKeylogStats, exportData } from '../services/api';

interface KeylogStats {
    total_sessions: number;
    total_duration_seconds: number;
    total_keystrokes: number;
    top_apps: { name: string, count: number }[];
}

const KeyloggerPanel: React.FC = () => {
    const [stats, setStats] = useState<KeylogStats | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        try {
            const response = await getKeylogStats();
            setStats(response.data);
        } catch (error) {
            console.error("Failed to fetch keylog stats", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
        // Refresh every 30s
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleExport = async (format: 'csv' | 'json') => {
        try {
            const response = await exportData(format, false);
            // Create blob link to download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `keylogs_export.${format}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error("Export failed", error);
        }
    };

    if (loading && !stats) return <div className="text-white">Loading Keylogger Data...</div>;

    const topAppsData = stats?.top_apps || [];

    return (
        <div className="space-y-6 animate-fadeIn">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white tracking-tight">Keylogger Management</h2>
                    <p className="text-slate-400 mt-1">Detailed analysis of user keyboard activity and application usage.</p>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={() => handleExport('csv')}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg flex items-center gap-2 transition-colors border border-slate-700"
                    >
                        <Download size={16} /> Export CSV
                    </button>
                    <button 
                        onClick={() => handleExport('json')}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg flex items-center gap-2 transition-colors border border-slate-700"
                    >
                        <Download size={16} /> Export JSON
                    </button>
                </div>
            </div>

            {/* Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        <Hash size={24} />
                    </div>
                    <div>
                        <p className="text-slate-400 text-xs uppercase font-mono">Total Keystrokes</p>
                        <p className="text-2xl font-bold text-white">{stats?.total_keystrokes.toLocaleString()}</p>
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                        <Keyboard size={24} />
                    </div>
                    <div>
                        <p className="text-slate-400 text-xs uppercase font-mono">Active Sessions</p>
                        <p className="text-2xl font-bold text-white">{stats?.total_sessions}</p>
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <Clock size={24} />
                    </div>
                    <div>
                        <p className="text-slate-400 text-xs uppercase font-mono">Total Duration</p>
                        <p className="text-2xl font-bold text-white">{((stats?.total_duration_seconds || 0) / 60).toFixed(0)}m</p>
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-pink-500/10 text-pink-400 border border-pink-500/20">
                        <Monitor size={24} />
                    </div>
                    <div>
                        <p className="text-slate-400 text-xs uppercase font-mono">Top App</p>
                        <p className="text-xl font-bold text-white truncate max-w-[150px]" title={topAppsData[0]?.name}>
                            {topAppsData[0]?.name || "N/A"}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Heatmap Section - Reusing Component */}
                <div className="lg:col-span-2">
                    <KeymapHeatmap />
                </div>

                {/* Top Apps Chart */}
                <div className="glass-panel p-6 rounded-xl border border-slate-800">
                    <h3 className="text-white font-bold mb-6 flex items-center gap-2">
                        <Monitor size={18} className="text-slate-400" /> Top Applications
                    </h3>
                    <div className="h-[300px] w-full">
                         <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topAppsData} layout="vertical" margin={{ left: 40 }}>
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} width={100} tickLine={false} axisLine={false} />
                                <Tooltip 
                                    contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc'}}
                                    cursor={{fill: 'rgba(255,255,255,0.05)'}}
                                />
                                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                                    {topAppsData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={index === 0 ? '#f472b6' : '#818cf8'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default KeyloggerPanel;