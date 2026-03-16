import React, { useEffect, useState, useMemo } from 'react';
import { io } from 'socket.io-client';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { API_BASE_URL, getKeylogStats } from '../services/api';

interface KeyStats {
    [key: string]: number;
}

const SOCKET_URL = API_BASE_URL;

const normalizeKey = (rawKey: string) => {
    const trimmed = String(rawKey || '').trim();
    const withoutPrefix = trimmed.replace(/^key\./i, '');
    return withoutPrefix.toUpperCase();
};

const KEYBOARD_LAYOUT = [
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'BACKSPACE'],
    ['TAB', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\'],
    ['CAPS', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'ENTER'],
    ['SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'SHIFT'],
    ['CTRL', 'WIN', 'ALT', 'SPACE', 'ALT', 'FN', 'CTRL']
];

const KeymapHeatmap: React.FC = () => {
    const [keyCounts, setKeyCounts] = useState<KeyStats>({});
    const [dwellTime, setDwellTime] = useState<KeyStats>({}); // Placeholder for now

    useEffect(() => {
        const loadHistoricalHeatmap = async () => {
            try {
                const response = await getKeylogStats();
                const historicalCounts = response?.data?.key_counts;
                if (!historicalCounts || typeof historicalCounts !== 'object') {
                    return;
                }
                setKeyCounts(prev => {
                    const next = { ...prev };
                    Object.entries(historicalCounts).forEach(([key, count]) => {
                        const normalized = normalizeKey(key);
                        next[normalized] = (next[normalized] || 0) + Number(count || 0);
                    });
                    return next;
                });
            } catch (_error) {
            }
        };

        loadHistoricalHeatmap();

        const socket = io(SOCKET_URL, {
            transports: ['websocket', 'polling'],
            withCredentials: true,
        });

        socket.on('connect', () => {
            console.log('Connected to socket for heatmap');
        });

        socket.on('key_heatmap_update', (data: any) => {
            // Data expected: { "a": 5, "b": 1, ... } (counts in this batch)
            // We accumulate them
            setKeyCounts(prev => {
                const next = { ...prev };
                Object.entries(data).forEach(([key, count]) => {
                    const k = normalizeKey(key);
                    next[k] = (next[k] || 0) + (count as number);
                });
                return next;
            });
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    // Determine max count for color scaling
    const maxCount = useMemo(() => {
        const values = Object.values(keyCounts);
        return values.length > 0 ? Math.max(...values) : 1;
    }, [keyCounts]);

    const getKeyColor = (key: string) => {
        const k = normalizeKey(key);
        const count = keyCounts[k] || 0;
        
        if (count === 0) return 'bg-slate-800 border-slate-700 text-slate-500';
        
        // Heatmap gradient logic
        const intensity = Math.min(count / maxCount, 1);
        
        if (intensity < 0.2) return 'bg-cyan-900/40 border-cyan-700 text-cyan-200 shadow-[0_0_10px_rgba(34,211,238,0.2)]';
        if (intensity < 0.5) return 'bg-cyan-600 border-cyan-400 text-white shadow-[0_0_15px_rgba(34,211,238,0.4)]';
        if (intensity < 0.8) return 'bg-purple-600 border-purple-400 text-white shadow-[0_0_20px_rgba(168,85,247,0.5)]';
        return 'bg-red-600 border-red-400 text-white shadow-[0_0_25px_rgba(239,68,68,0.6)] animate-pulse';
    };

    const getKeyWidth = (key: string) => {
        switch (key) {
            case 'BACKSPACE': return 'w-16';
            case 'TAB': return 'w-14';
            case 'CAPS': return 'w-16';
            case 'ENTER': return 'w-20';
            case 'SHIFT': return 'w-24';
            case 'SPACE': return 'w-64';
            case 'CTRL': return 'w-12';
            default: return 'w-10';
        }
    };

    // Prepare data for the bar chart
    const chartData = useMemo(() => {
        return Object.entries(keyCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10) // Top 10
            .map(([name, value]) => ({ name, value }));
    }, [keyCounts]);

    return (
        <div className="space-y-6">
            {/* Top Stats Section */}
            <div className="glass-panel p-6 rounded-xl border border-slate-800">
                <h3 className="text-white font-bold mb-4">Top Active Keys</h3>
                <div className="h-40 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                            <XAxis dataKey="name" stroke="#94a3b8" tick={{fontSize: 12}} />
                            <Tooltip 
                                contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc'}}
                                itemStyle={{color: '#38bdf8'}}
                            />
                            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={index < 3 ? '#f472b6' : '#38bdf8'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Keyboard Heatmap */}
            <div className="glass-panel p-8 rounded-xl border border-slate-800 flex flex-col items-center justify-center bg-slate-950 overflow-hidden">
                <h3 className="text-slate-400 text-sm font-mono uppercase tracking-widest mb-8">Full Spectrum Heatmap</h3>
                
                <div className="w-full overflow-x-auto pb-4">
                    <div className="flex flex-col gap-1 min-w-[700px] items-center">
                        {KEYBOARD_LAYOUT.map((row, rowIndex) => (
                            <div key={rowIndex} className="flex gap-1 justify-center w-full">
                                {row.map((key, keyIndex) => (
                                    <div
                                        key={`${rowIndex}-${keyIndex}-${key}`}
                                        className={`
                                            h-10 flex items-center justify-center rounded border flex-shrink-0
                                            text-[10px] font-bold transition-all duration-300
                                            ${getKeyWidth(key)}
                                            ${getKeyColor(key)}
                                        `}
                                    >
                                        {key}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>

                <div className="flex items-center gap-6 mt-4 text-xs text-slate-500 font-mono flex-wrap justify-center">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-slate-800 border border-slate-700"></div>
                        <span>IDLE</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-cyan-900/40 border border-cyan-700"></div>
                        <span>LOW</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-cyan-600 border border-cyan-400"></div>
                        <span>MED</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-purple-600 border border-purple-400"></div>
                        <span>HIGH</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-600 border border-red-400"></div>
                        <span>CRITICAL</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default KeymapHeatmap;
