import React, { useState } from 'react';
import { Search, Filter, Download } from 'lucide-react';
import { LogEntry, RiskLevel, ActivityType } from '../types';

interface ActivityLogProps {
    logs: LogEntry[];
}

const ActivityLog: React.FC<ActivityLogProps> = ({ logs }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [filterRisk, setFilterRisk] = useState<string>('ALL');

    const filteredLogs = logs.filter(log => {
        const matchesSearch = log.description.toLowerCase().includes(searchTerm.toLowerCase()) || 
                              log.user.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesRisk = filterRisk === 'ALL' || log.riskLevel === filterRisk;
        return matchesSearch && matchesRisk;
    });

    const handleExportCSV = () => {
        if (filteredLogs.length === 0) return;

        // CSV Header
        const headers = ["Timestamp", "User", "Activity Type", "Description", "Details", "Risk Level", "IP Address"];
        
        // Map logs to rows
        const rows = filteredLogs.map(log => [
            log.timestamp,
            log.user,
            log.activityType,
            `"${log.description.replace(/"/g, '""')}"`, // Escape quotes
            `"${log.details.replace(/"/g, '""')}"`,
            log.riskLevel,
            log.ipAddress || 'N/A'
        ]);

        // Combine
        const csvContent = "data:text/csv;charset=utf-8," 
            + headers.join(",") + "\n" 
            + rows.map(e => e.join(",")).join("\n");

        // Trigger Download
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `sentinel_logs_${new Date().toISOString()}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="space-y-6 h-full flex flex-col">
             <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">Live Activity Monitor</h2>
                    <p className="text-slate-400 mt-1 text-sm">Real-time stream of all user and system activities via secure socket.</p>
                </div>
                {/* Download Button moved here next to filters as requested in spirit, though technically header is distinct */}
            </div>

            {/* Toolbar */}
            <div className="glass-panel p-4 rounded-xl flex flex-wrap gap-4 items-center justify-between">
                <div className="relative flex-1 min-w-[200px] max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input 
                        type="text" 
                        placeholder="Search logs by user, event..." 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-slate-900/80 border border-slate-700 rounded-lg py-2 pl-10 pr-4 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
                    />
                </div>
                
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2">
                         <Filter className="text-slate-500" size={18} />
                        <select 
                            className="bg-transparent text-sm text-slate-300 focus:outline-none"
                            value={filterRisk}
                            onChange={(e) => setFilterRisk(e.target.value)}
                        >
                            <option value="ALL">All Risks</option>
                            <option value={RiskLevel.LOW}>Low</option>
                            <option value={RiskLevel.MEDIUM}>Medium</option>
                            <option value={RiskLevel.HIGH}>High</option>
                            <option value={RiskLevel.CRITICAL}>Critical</option>
                        </select>
                    </div>

                    <div className="h-8 w-px bg-slate-700 mx-2" />

                    <button 
                        onClick={handleExportCSV}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm font-medium border border-slate-700"
                    >
                        <Download size={16} />
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="glass-panel rounded-xl overflow-hidden flex-1 border border-slate-800">
                <div className="overflow-auto h-full">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-slate-900 text-slate-400 text-xs uppercase font-mono sticky top-0 z-10">
                            <tr>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Status</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Timestamp</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">User</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Activity Type</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Details</th>
                                <th className="px-6 py-4 font-medium border-b border-slate-800">Origin</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {filteredLogs.map((log) => (
                                <tr key={log.id} className="hover:bg-slate-800/20 transition-colors group animate-fadeIn">
                                    <td className="px-6 py-4">
                                        <div className={`w-2 h-2 rounded-full 
                                            ${log.riskLevel === RiskLevel.CRITICAL ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse' : 
                                              log.riskLevel === RiskLevel.HIGH ? 'bg-orange-500' : 
                                              log.riskLevel === RiskLevel.MEDIUM ? 'bg-yellow-500' : 'bg-blue-500'}`} 
                                        />
                                    </td>
                                    <td className="px-6 py-4 text-slate-400 text-sm font-mono whitespace-nowrap">
                                        {new Date(log.timestamp).toLocaleTimeString()}
                                    </td>
                                    <td className="px-6 py-4 text-white text-sm font-medium">
                                        <div className="flex items-center gap-2">
                                            <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-300">
                                                {log.user.substring(0,2).toUpperCase()}
                                            </div>
                                            {log.user}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-[10px] font-mono border border-slate-700 px-2 py-0.5 rounded text-slate-400 bg-slate-900">
                                            {log.activityType}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="max-w-xs">
                                            <p className="text-slate-200 text-sm truncate" title={log.description}>{log.description}</p>
                                            <p className="text-slate-500 text-xs truncate font-mono mt-0.5" title={log.details}>{log.details}</p>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-slate-400 text-xs font-mono">
                                        {log.ipAddress}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {filteredLogs.length === 0 && (
                        <div className="p-12 text-center text-slate-500">
                            No logs found matching criteria.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ActivityLog;