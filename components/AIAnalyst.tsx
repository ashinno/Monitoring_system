import React, { useState } from 'react';
import { BrainCircuit, Sparkles, AlertTriangle, CheckCircle, MessageSquare, Download } from 'lucide-react';
import { chatWithAnalyst } from '../services/geminiService';
import { AnalysisResult } from '../types';
import API from '../services/api';

const AIAnalyst: React.FC = () => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [chatInput, setChatInput] = useState('');
    const [chatHistory, setChatHistory] = useState<{role: 'user' | 'ai', text: string}[]>([]);
    const [isChatting, setIsChatting] = useState(false);

    const handleRunAnalysis = async () => {
        setIsAnalyzing(true);
        try {
            const response = await API.post('/analyze');
            setResult(response.data);
        } catch (e) {
            console.error(e);
            alert("Failed to run AI analysis. Please check console.");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSendMessage = async () => {
        if (!chatInput.trim()) return;
        
        const userMsg = chatInput;
        setChatInput('');
        setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
        setIsChatting(true);

        // We can keep chatWithAnalyst as is if it calls an external service or mock
        // Since backend instructions didn't mention chat endpoint, we assume it's still external/mock.
        const aiResponse = await chatWithAnalyst(userMsg, []); 
        
        setChatHistory(prev => [...prev, { role: 'ai', text: aiResponse }]);
        setIsChatting(false);
    };

    const handleExportReport = () => {
        if (!result) return;

        const timestamp = new Date().toLocaleString();
        const reportContent = `
SENTINEL AI - SECURITY ANALYSIS REPORT
Generated: ${timestamp}
--------------------------------------------------

THREAT SCORE: ${result.threatScore}/100
Status: ${result.threatScore > 70 ? 'CRITICAL' : result.threatScore > 30 ? 'ELEVATED' : 'STABLE'}

EXECUTIVE SUMMARY:
${result.summary}

RECOMMENDATIONS:
${result.recommendations.map((rec, i) => `${i + 1}. ${rec}`).join('\n')}

--------------------------------------------------
CONFIDENTIAL - INTERNAL USE ONLY
        `.trim();

        const blob = new Blob([reportContent], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Sentinel_Analysis_${new Date().toISOString().slice(0,10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            {/* Left Col: Control & Report */}
            <div className="lg:col-span-2 space-y-6 flex flex-col">
                <div className="glass-panel p-8 rounded-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                    
                    <div className="relative z-10">
                        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                            <BrainCircuit className="text-cyan-400" />
                            Sentinel AI Analyst
                        </h2>
                        <p className="text-slate-400 max-w-lg mb-6">
                            Leverage Local Heuristic Engine (Pandas) to deep-scan activity logs for anomalies and policy violations.
                        </p>
                        
                        <button 
                            onClick={handleRunAnalysis}
                            disabled={isAnalyzing}
                            className={`px-6 py-3 rounded-lg font-bold flex items-center gap-2 transition-all shadow-neon
                                ${isAnalyzing ? 'bg-slate-700 cursor-not-allowed text-slate-400' : 'bg-cyan-600 hover:bg-cyan-500 text-white'}`}
                        >
                            {isAnalyzing ? (
                                <>
                                    <Sparkles className="animate-spin" size={20} />
                                    Analyzing Logs...
                                </>
                            ) : (
                                <>
                                    <Sparkles size={20} />
                                    Run Deep Scan Analysis
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Analysis Result */}
                {result && (
                    <div className="flex-1 glass-panel p-6 rounded-xl animate-fadeIn overflow-auto border-t-4 border-t-cyan-500">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h3 className="text-xl font-bold text-white">Analysis Report</h3>
                                <p className="text-slate-500 text-sm font-mono">ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}</p>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                                <div className="flex flex-col items-end">
                                    <span className="text-xs text-slate-400 uppercase tracking-widest mb-1">Threat Score</span>
                                    <div className={`text-3xl font-bold font-mono ${
                                        result.threatScore > 70 ? 'text-red-500' : result.threatScore > 30 ? 'text-yellow-500' : 'text-green-500'
                                    }`}>
                                        {result.threatScore}/100
                                    </div>
                                </div>
                                <button 
                                    onClick={handleExportReport}
                                    className="flex items-center gap-2 text-xs text-cyan-400 hover:text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/10 px-3 py-1.5 rounded transition-colors"
                                >
                                    <Download size={14} />
                                    Export Report
                                </button>
                            </div>
                        </div>

                        <div className="space-y-6">
                            <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                                <h4 className="text-cyan-400 text-sm font-bold uppercase tracking-wider mb-2">Executive Summary</h4>
                                <p className="text-slate-300 leading-relaxed">{result.summary}</p>
                            </div>

                            <div>
                                <h4 className="text-white font-bold mb-3 flex items-center gap-2">
                                    <CheckCircle size={16} className="text-green-400" />
                                    AI Recommendations
                                </h4>
                                <ul className="space-y-2">
                                    {result.recommendations.map((rec, idx) => (
                                        <li key={idx} className="flex gap-3 text-slate-300 bg-slate-800/30 p-3 rounded hover:bg-slate-800/50 transition-colors">
                                            <span className="text-cyan-500 font-mono text-sm">0{idx + 1}</span>
                                            {rec}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Right Col: Chat Interface */}
            <div className="glass-panel flex flex-col rounded-xl overflow-hidden h-[600px] lg:h-auto">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                    <h3 className="text-white font-bold flex items-center gap-2">
                        <MessageSquare size={18} className="text-cyan-400" />
                        Analyst Chat
                    </h3>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-950/30">
                    {chatHistory.length === 0 && (
                        <div className="text-center text-slate-600 mt-10 text-sm">
                            <p>Ask me anything about the current security posture or specific user activity.</p>
                        </div>
                    )}
                    {chatHistory.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[85%] p-3 rounded-lg text-sm ${
                                msg.role === 'user' 
                                    ? 'bg-cyan-600/20 text-cyan-100 border border-cyan-500/30 rounded-br-none' 
                                    : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none'
                            }`}>
                                {msg.text}
                            </div>
                        </div>
                    ))}
                     {isChatting && (
                         <div className="flex justify-start">
                             <div className="bg-slate-800 p-3 rounded-lg rounded-bl-none">
                                <div className="flex gap-1">
                                    <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                                    <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                                    <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
                                </div>
                             </div>
                         </div>
                     )}
                    
                    <div className="mt-4 border-t border-slate-800 pt-4">
                        <div className="flex gap-2">
                            <input 
                                type="text" 
                                value={chatInput}
                                onChange={(e) => setChatInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                                placeholder="Type your query..."
                                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                            />
                            <button 
                                onClick={handleSendMessage}
                                disabled={!chatInput.trim() || isChatting}
                                className="bg-cyan-600 hover:bg-cyan-500 text-white p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <MessageSquare size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AIAnalyst;
