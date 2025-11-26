import React, { useEffect, useState } from 'react';
import { Activity, AlertTriangle, RefreshCw, ShieldCheck, Server } from 'lucide-react';
import { getNetworkAnalysis } from '../services/api';
import { NetworkAnalysisResult } from '../types';

const NetworkAnalysis: React.FC = () => {
    const [analysis, setAnalysis] = useState<NetworkAnalysisResult | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAnalysis = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getNetworkAnalysis();
            // Map snake_case response to camelCase if needed, but backend schemas use camelCase aliases? 
            // Wait, in main.py I used `response_model=schemas.NetworkAnalysisResult`. 
            // schemas.py has `alias_generator=to_camel`. So the JSON response keys will be camelCase.
            // My types.ts uses snake_case for NetworkTraffic but snake_case for AnalysisResult?
            // Let's check types.ts again. 
            // types.ts: NetworkAnalysisResult { anomaly_score, anomalies_detected, ... } (snake_case)
            // schemas.py: NetworkAnalysisResult ... (Pydantic models)
            // If Pydantic uses to_camel, then `anomaly_score` becomes `anomalyScore`.
            // So I need to match my frontend types to what the API actually returns (camelCase) OR adjust how I consume it.
            
            // Let's assume the API returns camelCase because of `alias_generator=to_camel`.
            // So `anomaly_score` -> `anomalyScore`.
            // My types.ts has `anomaly_score`. This is a mismatch. 
            // I should update types.ts to camelCase or cast/map it here.
            // Actually, for simplicity, I'll update types.ts to match the expected API response (camelCase).
            
            // Wait, I should verify what the API returns. 
            // `test_network_analysis.py` output: 'anomalyScore': 9.52, 'anomaliesDetected': 2
            // Yes, it returns camelCase.
            
            setAnalysis(response.data);
        } catch (err) {
            console.error("Failed to fetch network analysis", err);
            setError("Failed to load network analysis data.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalysis();
    }, []);

    if (loading) {
        return (
            <div className="glass-panel p-6 rounded-xl flex items-center justify-center h-64">
                <div className="animate-spin text-cyan-400">
                    <RefreshCw size={32} />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass-panel p-6 rounded-xl border border-red-500/30 bg-red-500/5">
                <div className="flex items-center gap-3 text-red-400">
                    <AlertTriangle />
                    <span>{error}</span>
                </div>
                <button 
                    onClick={fetchAnalysis}
                    className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm text-white transition-colors"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!analysis) return null;

    return (
        <div className="glass-panel p-6 rounded-xl animate-fadeIn">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Activity className="text-cyan-400" size={20} />
                        Network Traffic Analysis
                    </h3>
                    <p className="text-slate-400 text-sm mt-1">{analysis.summary}</p>
                </div>
                <button 
                    onClick={fetchAnalysis} 
                    className="p-2 hover:bg-slate-700 rounded-full text-slate-400 hover:text-white transition-colors"
                    title="Refresh Analysis"
                >
                    <RefreshCw size={16} />
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-xs font-mono mb-1">Anomaly Score</div>
                    <div className={`text-2xl font-bold font-mono ${analysis.anomalyScore > 50 ? 'text-red-400' : analysis.anomalyScore > 20 ? 'text-yellow-400' : 'text-green-400'}`}>
                        {analysis.anomalyScore}%
                    </div>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-xs font-mono mb-1">Anomalies Detected</div>
                    <div className="text-2xl font-bold font-mono text-white">
                        {analysis.anomaliesDetected}
                    </div>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-xs font-mono mb-1">Status</div>
                    <div className="flex items-center gap-2 mt-1">
                        {analysis.anomaliesDetected === 0 ? (
                            <>
                                <ShieldCheck className="text-green-400" size={20} />
                                <span className="text-green-400 font-bold">SECURE</span>
                            </>
                        ) : (
                            <>
                                <AlertTriangle className="text-red-400" size={20} />
                                <span className="text-red-400 font-bold">WARNING</span>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {analysis.details.length > 0 && (
                <div className="mt-6">
                    <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                        <Server size={14} />
                        Detected Anomalies
                    </h4>
                    <div className="space-y-2">
                        {analysis.details.map((detail, idx) => (
                            <div key={idx} className="bg-slate-900/30 border border-red-500/20 rounded-lg p-3 hover:bg-slate-800/50 transition-colors">
                                <div className="flex justify-between items-start">
                                    <span className="text-red-400 font-mono text-sm font-bold">{detail.type}</span>
                                    <span className="text-slate-500 text-xs font-mono">{detail.value}</span>
                                </div>
                                <div className="flex items-center gap-4 mt-2 text-xs text-slate-400 font-mono">
                                    <div><span className="text-slate-600">SRC:</span> {detail.source}</div>
                                    <div className="text-slate-600">→</div>
                                    <div><span className="text-slate-600">DST:</span> {detail.destination}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default NetworkAnalysis;
