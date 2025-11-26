import React, { useEffect, useState } from 'react';
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, Cell, Legend
} from 'recharts';
import { ShieldAlert, Globe, Users, BrainCircuit, Sparkles, PieChart } from 'lucide-react';
import { LogEntry, RiskLevel, NetworkTraffic, PredictionResult } from '../types';
import { getNetworkTraffic } from '../services/api';
import NetworkAnalysis from './NetworkAnalysis';
import NetworkGraph from './NetworkGraph';
import TrafficSimulator from './TrafficSimulator';
import { io } from 'socket.io-client';

interface DashboardProps {
    logs: LogEntry[];
}

// Custom Tooltip Component for Cyber Look
const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-slate-900/90 border border-slate-700 p-3 rounded-lg shadow-xl backdrop-blur-md">
                <p className="text-slate-300 font-mono text-xs mb-2 border-b border-slate-800 pb-1">{label}</p>
                {payload.map((p: any, index: number) => (
                    <div key={index} className="flex items-center gap-2 text-xs font-medium mb-1">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
                        <span className="text-slate-400">{p.name}:</span>
                        <span className="text-slate-100 font-mono">{p.value}</span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

// Generate mock chart data (static for visual demo, but could be dynamic)
const trafficData = Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    inbound: Math.floor(Math.random() * 100) + 20,
    outbound: Math.floor(Math.random() * 80) + 10,
}));

const Dashboard: React.FC<DashboardProps> = ({ logs }) => {
    const [chartData, setChartData] = useState<any[]>(trafficData);
    const [trafficLogs, setTrafficLogs] = useState<NetworkTraffic[]>([]);
    const [prediction, setPrediction] = useState<PredictionResult | null>(null);

    useEffect(() => {
        const fetchTraffic = async () => {
            try {
                const response = await getNetworkTraffic();
                if (response.data) {
                    setTrafficLogs(response.data);
                }
            } catch (error) {
                console.error("Failed to fetch traffic logs", error);
            }
        };
        fetchTraffic();

        // Socket connection for real-time traffic
        const socket = io('http://localhost:8000');
        socket.on('new_traffic', (data: NetworkTraffic) => {
             setTrafficLogs(prev => {
                 const updated = [...prev, data];
                 // Keep manageable size
                 if (updated.length > 5000) return updated.slice(-5000);
                 return updated;
             });
        });

        socket.on('prediction_update', (data: PredictionResult) => {
            setPrediction(data);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    useEffect(() => {
        if (trafficLogs.length > 0) {
            processTrafficData(trafficLogs);
        }
    }, [trafficLogs]);

    const processTrafficData = (data: NetworkTraffic[]) => {
        // Group by hour:minute
        const grouped: {[key: string]: {inbound: number, outbound: number}} = {};
        
        // Sort by timestamp asc
        const sorted = [...data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

        sorted.forEach(t => {
            const date = new Date(t.timestamp);
            const timeKey = `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
            
            if (!grouped[timeKey]) {
                grouped[timeKey] = { inbound: 0, outbound: 0 };
            }
            
            // Simple logic: if dest is internal (starts with 192.168), it's inbound. Else outbound.
            // Adjust based on actual data patterns.
            if (t.destinationIp.startsWith('192.168')) {
                grouped[timeKey].inbound += t.bytesTransferred;
            } else {
                grouped[timeKey].outbound += t.bytesTransferred;
            }
        });

        // Convert to array
        const processed = Object.keys(grouped).map(key => ({
            time: key,
            inbound: grouped[key].inbound,
            outbound: grouped[key].outbound
        }));

        // If not enough data, pad with previous mock-like logic or just show what we have
        if (processed.length > 0) {
            setChartData(processed);
        } else {
            // Fallback to mock if empty
            setChartData(trafficData);
        }
    };

    // Dynamic Calculations
    const threatsBlocked = logs.filter(l => l.riskLevel === RiskLevel.HIGH || l.riskLevel === RiskLevel.CRITICAL).length;
    const activeUsers = new Set(logs.map(l => l.user)).size;
    const aiAnomalies = Math.floor(threatsBlocked * 0.85); // Mocking that 85% of threats were detected by AI
    
    // Risk Counts for Breakdown Card
    const totalLogs = logs.length || 1;
    const riskCounts = {
        [RiskLevel.LOW]: logs.filter(l => l.riskLevel === RiskLevel.LOW).length,
        [RiskLevel.MEDIUM]: logs.filter(l => l.riskLevel === RiskLevel.MEDIUM).length,
        [RiskLevel.HIGH]: logs.filter(l => l.riskLevel === RiskLevel.HIGH).length,
        [RiskLevel.CRITICAL]: logs.filter(l => l.riskLevel === RiskLevel.CRITICAL).length,
    };

    const riskDistribution = [
        { name: 'Low', value: riskCounts[RiskLevel.LOW], color: '#3b82f6' },
        { name: 'Medium', value: riskCounts[RiskLevel.MEDIUM], color: '#eab308' },
        { name: 'High', value: riskCounts[RiskLevel.HIGH], color: '#f97316' },
        { name: 'Critical', value: riskCounts[RiskLevel.CRITICAL], color: '#ef4444' },
    ];

    return (
        <div className="space-y-6 animate-fadeIn">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold text-white tracking-tight">System Status</h2>
                    <p className="text-slate-400 mt-1">Real-time overview of network security and user activity.</p>
                </div>
                <div className="flex gap-2">
                    <span className="px-3 py-1 rounded-full bg-green-500/10 border border-green-500/30 text-green-400 text-xs font-mono flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"/>
                        LIVE FEED
                    </span>
                    <span className="px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-xs font-mono">
                        {(new Date()).toLocaleTimeString()}
                    </span>
                </div>
            </div>

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                {[
                    { title: "Threats Detected", val: threatsBlocked, icon: <ShieldAlert className="text-red-400" />, trend: "+12%" },
                    { title: "Active Users", val: activeUsers, icon: <Users className="text-cyan-400" />, trend: "stable" },
                    { title: "AI Anomalies", val: aiAnomalies, icon: <BrainCircuit className="text-purple-400" />, trend: "98% acc." },
                    { title: "False Positive Rate", val: "0.4%", icon: <Sparkles className="text-pink-400" />, trend: "-0.1%" },
                ].map((stat, idx) => (
                    <div key={idx} className="glass-panel p-5 rounded-xl hover:bg-slate-800/50 transition-colors">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                                {stat.icon}
                            </div>
                            <span className={`text-xs font-mono ${stat.trend === 'stable' ? 'text-slate-400' : stat.trend.includes('-') ? 'text-green-400' : stat.trend.includes('acc') ? 'text-purple-400' : 'text-red-400'}`}>
                                {stat.trend}
                            </span>
                        </div>
                        <h3 className="text-slate-400 text-sm font-medium">{stat.title}</h3>
                        <p className="text-2xl font-bold text-white font-mono mt-1">{stat.val}</p>
                    </div>
                ))}

                {/* New Compact Threat Breakdown Card */}
                <div className="glass-panel p-5 rounded-xl hover:bg-slate-800/50 transition-colors flex flex-col justify-between">
                    <div className="flex justify-between items-start mb-2">
                         <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                                <PieChart className="text-orange-400" />
                        </div>
                        <span className="text-xs font-mono text-slate-400">Total: {totalLogs}</span>
                    </div>
                    <div>
                         <h3 className="text-slate-400 text-sm font-medium mb-3">Threat Breakdown</h3>
                         {/* Mini Stacked Bar */}
                         <div className="h-4 w-full flex rounded overflow-hidden mb-2">
                            <div style={{ width: `${(riskCounts.LOW / totalLogs) * 100}%` }} className="bg-blue-500 h-full" title="Low" />
                            <div style={{ width: `${(riskCounts.MEDIUM / totalLogs) * 100}%` }} className="bg-yellow-500 h-full" title="Medium" />
                            <div style={{ width: `${(riskCounts.HIGH / totalLogs) * 100}%` }} className="bg-orange-500 h-full" title="High" />
                            <div style={{ width: `${(riskCounts.CRITICAL / totalLogs) * 100}%` }} className="bg-red-500 h-full" title="Critical" />
                         </div>
                         <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                             <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-blue-500"/>Lo</span>
                             <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-yellow-500"/>Med</span>
                             <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-orange-500"/>Hi</span>
                             <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-red-500"/>Cri</span>
                         </div>
                    </div>
                </div>

                {/* Prediction Card */}
                <div className="glass-panel p-5 rounded-xl hover:bg-slate-800/50 transition-colors flex flex-col justify-between">
                    <div className="flex justify-between items-start mb-2">
                        <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                            <Sparkles className="text-indigo-400" />
                        </div>
                        <span className="text-xs font-mono text-indigo-400">AI PREDICT</span>
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium">Predicted Next Move</h3>
                    {prediction ? (
                        <div className="mt-3 space-y-2">
                            <div className="flex justify-between text-xs text-slate-500">
                                <span>Current: {prediction.currentActivity}</span>
                            </div>
                            {prediction.predictions.map((p, idx) => (
                                <div key={idx} className="flex justify-between items-center text-sm">
                                    <span className="text-slate-300">{p.activity}</span>
                                    <span className={`font-mono ${p.probability > 0.8 ? 'text-red-400' : 'text-slate-400'}`}>
                                        {(p.probability * 100).toFixed(0)}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-500 text-sm mt-2">Waiting for activity...</p>
                    )}
                </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-panel p-6 rounded-xl">
                    <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                        <Globe size={18} className="text-cyan-400" />
                        Network Traffic Overview
                    </h3>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorIn" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorOut" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend verticalAlign="top" height={36} iconType="circle" />
                                <Area name="Inbound Traffic" type="monotone" dataKey="inbound" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#colorIn)" />
                                <Area name="Outbound Traffic" type="monotone" dataKey="outbound" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorOut)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="glass-panel p-6 rounded-xl flex flex-col">
                    <h3 className="text-lg font-semibold text-white mb-6">Threat Distribution</h3>
                    <div className="flex-1 w-full relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={riskDistribution} layout="vertical" barSize={20}>
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} width={60} tickLine={false} axisLine={false} />
                                <Tooltip content={<CustomTooltip />} cursor={{fill: 'transparent'}} />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                    {riskDistribution.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Recent Alerts Table (Mini) */}
            <div className="glass-panel rounded-xl overflow-hidden">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">Recent Critical Events</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-slate-900/50 text-slate-400 text-xs uppercase font-mono">
                            <tr>
                                <th className="px-6 py-4 font-medium">Timestamp</th>
                                <th className="px-6 py-4 font-medium">User</th>
                                <th className="px-6 py-4 font-medium">Event</th>
                                <th className="px-6 py-4 font-medium">Risk</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {logs.filter(l => l.riskLevel !== RiskLevel.LOW).slice(0, 3).map((log) => (
                                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                                    <td className="px-6 py-4 text-slate-400 text-sm font-mono">{new Date(log.timestamp).toLocaleTimeString()}</td>
                                    <td className="px-6 py-4 text-white text-sm">{log.user}</td>
                                    <td className="px-6 py-4 text-slate-300 text-sm">
                                        <div className="flex flex-col">
                                            <span>{log.description}</span>
                                            <span className="text-xs text-slate-500">{log.details}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase border
                                            ${log.riskLevel === RiskLevel.CRITICAL ? 'bg-red-500/10 text-red-400 border-red-500/50' : 
                                              log.riskLevel === RiskLevel.HIGH ? 'bg-orange-500/10 text-orange-400 border-orange-500/50' : 
                                              'bg-yellow-500/10 text-yellow-400 border-yellow-500/50'}`}>
                                            {log.riskLevel}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Network Analysis Module */}
            <NetworkGraph logs={logs} />
            <TrafficSimulator />
            <NetworkAnalysis />
        </div>
    );
};

export default Dashboard;