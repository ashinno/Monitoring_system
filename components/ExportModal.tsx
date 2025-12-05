import React, { useState } from 'react';
import { X, FileText, Table, FileJson, Download, Archive } from 'lucide-react';
import { exportData } from '../services/api';

interface ExportModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose }) => {
    const [format, setFormat] = useState<string>('csv');
    const [startDate, setStartDate] = useState<string>('');
    const [endDate, setEndDate] = useState<string>('');
    const [compress, setCompress] = useState(false);
    const [loading, setLoading] = useState(false);

    if (!isOpen) return null;

    const handleExport = async () => {
        setLoading(true);
        try {
            const response = await exportData(format, compress, startDate, endDate);
            
            // Create Blob from response data
            const type = compress ? 'application/zip' : (format === 'pdf' ? 'application/pdf' : format === 'json' ? 'application/json' : 'text/csv');
            const ext = compress ? 'zip' : format;
            
            const blob = new Blob([response.data], { type });
            
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `sentinel_report_${new Date().toISOString().slice(0,10)}.${ext}`);
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            onClose();
        } catch (error) {
            console.error("Export failed", error);
            alert("Export failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl animate-fadeIn">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold text-white">Export Data</h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="space-y-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">Format</label>
                        <div className="grid grid-cols-3 gap-3">
                            <button 
                                onClick={() => setFormat('csv')}
                                className={`flex flex-col items-center justify-center p-3 rounded-lg border transition-all ${format === 'csv' ? 'bg-blue-500/20 border-blue-500 text-blue-400' : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-750'}`}
                            >
                                <Table size={20} className="mb-2" />
                                <span className="text-xs font-mono">CSV</span>
                            </button>
                            <button 
                                onClick={() => setFormat('json')}
                                className={`flex flex-col items-center justify-center p-3 rounded-lg border transition-all ${format === 'json' ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400' : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-750'}`}
                            >
                                <FileJson size={20} className="mb-2" />
                                <span className="text-xs font-mono">JSON</span>
                            </button>
                            <button 
                                onClick={() => setFormat('pdf')}
                                className={`flex flex-col items-center justify-center p-3 rounded-lg border transition-all ${format === 'pdf' ? 'bg-red-500/20 border-red-500 text-red-400' : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-750'}`}
                            >
                                <FileText size={20} className="mb-2" />
                                <span className="text-xs font-mono">PDF</span>
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">Date Range (Optional)</label>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="text-xs text-slate-500 mb-1 block">Start Date</label>
                                <input 
                                    type="date" 
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 mb-1 block">End Date</label>
                                <input 
                                    type="date" 
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="pt-2">
                        <label className="flex items-center gap-3 p-3 rounded-lg border border-slate-700 bg-slate-800/30 cursor-pointer hover:bg-slate-800/50 transition-colors">
                            <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${compress ? 'bg-blue-500 border-blue-500' : 'border-slate-500'}`}>
                                {compress && <Archive size={12} className="text-white" />}
                            </div>
                            <input 
                                type="checkbox" 
                                checked={compress}
                                onChange={(e) => setCompress(e.target.checked)}
                                className="hidden"
                            />
                            <div>
                                <span className="text-sm text-slate-200 font-medium block">Compress Export</span>
                                <span className="text-xs text-slate-500 block">Save as .zip archive (Recommended for large exports)</span>
                            </div>
                        </label>
                    </div>
                </div>

                <button 
                    onClick={handleExport}
                    disabled={loading}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            Processing...
                        </>
                    ) : (
                        <>
                            <Download size={18} />
                            Download Export
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default ExportModal;
