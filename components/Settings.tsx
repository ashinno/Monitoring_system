import React, { useState, useEffect } from 'react';
import { Shield, Lock, Eye, Bell, Save, AlertTriangle, X, CheckCircle, Plus, Trash2 } from 'lucide-react';
import API from '../services/api';

const Settings: React.FC = () => {
    const [settings, setSettings] = useState({
        blockGambling: true,
        blockSocialMedia: false,
        enforceSafeSearch: true,
        screenTimeLimit: true,
        alertOnKeywords: true,
        captureScreenshots: false,
        keywords: [] as string[]
    });
    const [newKeyword, setNewKeyword] = useState("");
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'IDLE' | 'SAVING' | 'SAVED'>('IDLE');

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const response = await API.get('/settings');
                if (response.data) {
                    const { id, ...rest } = response.data;
                    setSettings(prev => ({ ...prev, ...rest }));
                }
            } catch (error) {
                console.error("Failed to fetch settings", error);
            }
        };
        fetchSettings();
    }, []);

    const toggle = (key: keyof typeof settings) => {
        setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const addKeyword = () => {
        if (newKeyword.trim() && !settings.keywords.includes(newKeyword.trim())) {
            setSettings(prev => ({
                ...prev,
                keywords: [...prev.keywords, newKeyword.trim()]
            }));
            setNewKeyword("");
        }
    };

    const removeKeyword = (word: string) => {
        setSettings(prev => ({
            ...prev,
            keywords: prev.keywords.filter(k => k !== word)
        }));
    };

    const handleSaveClick = () => {
        setIsModalOpen(true);
    };

    const confirmSave = async () => {
        setSaveStatus('SAVING');
        try {
            await API.put('/settings', settings);
            setSaveStatus('SAVED');
            setIsModalOpen(false);
            setTimeout(() => setSaveStatus('IDLE'), 4000);
        } catch (error) {
            console.error("Failed to save settings", error);
            setSaveStatus('IDLE');
            setIsModalOpen(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn relative">
            
            {/* Success Feedback Banner */}
            {saveStatus === 'SAVED' && (
                <div className="absolute -top-12 left-0 right-0 z-20 animate-slideDown">
                    <div className="bg-green-500/10 backdrop-blur-md border border-green-500/40 text-green-400 p-3 rounded-lg flex items-center justify-center gap-3 shadow-[0_0_15px_rgba(34,197,94,0.2)]">
                        <CheckCircle size={20} />
                        <span className="font-semibold">Settings saved successfully! System policies have been updated.</span>
                    </div>
                </div>
            )}

            <div>
                <h2 className="text-2xl font-bold text-white">Policy Control Center</h2>
                <p className="text-slate-400 mt-1">Configure automated enforcement rules and monitoring privacy settings.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Content Filtering */}
                <div className="glass-panel p-6 rounded-xl border-t-4 border-t-cyan-500">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-slate-900 rounded border border-slate-800 text-cyan-400">
                            <Shield size={20} />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Content Filtering</h3>
                    </div>
                    
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg">
                            <div>
                                <p className="text-slate-200 font-medium">Block Gambling/Adult</p>
                                <p className="text-slate-500 text-xs">Restrict access to high-risk categories</p>
                            </div>
                            <button 
                                onClick={() => toggle('blockGambling')}
                                className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.blockGambling ? 'bg-cyan-600' : 'bg-slate-700'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.blockGambling ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>
                        
                        <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg">
                            <div>
                                <p className="text-slate-200 font-medium">Block Social Media</p>
                                <p className="text-slate-500 text-xs">Limit productivity distractions</p>
                            </div>
                            <button 
                                onClick={() => toggle('blockSocialMedia')}
                                className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.blockSocialMedia ? 'bg-cyan-600' : 'bg-slate-700'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.blockSocialMedia ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>

                         <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg">
                            <div>
                                <p className="text-slate-200 font-medium">Force SafeSearch</p>
                                <p className="text-slate-500 text-xs">Enforce strict mode on search engines</p>
                            </div>
                            <button 
                                onClick={() => toggle('enforceSafeSearch')}
                                className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.enforceSafeSearch ? 'bg-cyan-600' : 'bg-slate-700'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.enforceSafeSearch ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Monitoring Depth */}
                <div className="glass-panel p-6 rounded-xl border-t-4 border-t-purple-500">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-slate-900 rounded border border-slate-800 text-purple-400">
                            <Eye size={20} />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Surveillance Level</h3>
                    </div>
                    
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg">
                            <div>
                                <p className="text-slate-200 font-medium">Screen Time Limits</p>
                                <p className="text-slate-500 text-xs">Auto-lock after designated hours</p>
                            </div>
                            <button 
                                onClick={() => toggle('screenTimeLimit')}
                                className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.screenTimeLimit ? 'bg-purple-600' : 'bg-slate-700'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.screenTimeLimit ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>
                        
                        <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg">
                            <div>
                                <p className="text-slate-200 font-medium">Periodic Screenshots</p>
                                <p className="text-slate-500 text-xs">Capture screen every 5 minutes (Privacy Risk)</p>
                            </div>
                            <button 
                                onClick={() => toggle('captureScreenshots')}
                                className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.captureScreenshots ? 'bg-purple-600' : 'bg-slate-700'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.captureScreenshots ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Notifications */}
                <div className="glass-panel p-6 rounded-xl border-t-4 border-t-yellow-500 md:col-span-2">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-slate-900 rounded border border-slate-800 text-yellow-400">
                            <Bell size={20} />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Alert Configuration</h3>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 bg-slate-900/40 rounded-lg">
                        <div className="flex-1">
                            <p className="text-slate-200 font-medium">Keyword Triggers</p>
                            <p className="text-slate-500 text-xs">Alert admin immediately if sensitive words are detected.</p>
                        </div>
                         <button 
                            onClick={() => toggle('alertOnKeywords')}
                            className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.alertOnKeywords ? 'bg-yellow-600' : 'bg-slate-700'}`}
                        >
                            <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.alertOnKeywords ? 'translate-x-6' : 'translate-x-0'}`} />
                        </button>
                    </div>

                    {settings.alertOnKeywords && (
                        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
                            <h4 className="text-slate-300 text-sm font-semibold mb-3">Monitored Keywords</h4>
                            
                            <div className="flex gap-2 mb-3">
                                <input 
                                    type="text" 
                                    value={newKeyword}
                                    onChange={(e) => setNewKeyword(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                                    placeholder="Enter keyword (e.g., confidential)"
                                    className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-yellow-500"
                                />
                                <button 
                                    onClick={addKeyword}
                                    className="bg-yellow-600 hover:bg-yellow-500 text-white p-1.5 rounded transition-colors"
                                >
                                    <Plus size={18} />
                                </button>
                            </div>

                            <div className="flex flex-wrap gap-2">
                                {settings.keywords?.map((word, idx) => (
                                    <div key={idx} className="bg-slate-800 border border-slate-700 rounded-full px-3 py-1 text-xs text-slate-300 flex items-center gap-2 group">
                                        {word}
                                        <button 
                                            onClick={() => removeKeyword(word)}
                                            className="text-slate-500 hover:text-red-400 opacity-60 group-hover:opacity-100 transition-opacity"
                                        >
                                            <X size={12} />
                                        </button>
                                    </div>
                                ))}
                                {settings.keywords?.length === 0 && (
                                    <span className="text-slate-600 text-xs italic">No keywords configured</span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="flex justify-end pt-4">
                <button 
                    onClick={handleSaveClick}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg font-bold flex items-center gap-2 transition-all shadow-neon"
                >
                    <Save size={18} />
                    {saveStatus === 'SAVED' ? 'Configuration Saved' : 'Save Configuration'}
                </button>
            </div>

            {/* Confirmation Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setIsModalOpen(false)} />
                    
                    <div className="relative bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full shadow-2xl animate-fadeIn">
                        <button 
                            onClick={() => setIsModalOpen(false)}
                            className="absolute top-4 right-4 text-slate-500 hover:text-white"
                        >
                            <X size={20} />
                        </button>

                        <div className="flex items-center gap-4 mb-4">
                            <div className="w-12 h-12 rounded-full bg-yellow-500/10 flex items-center justify-center border border-yellow-500/30">
                                <AlertTriangle className="text-yellow-500" size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Confirm Changes</h3>
                                <p className="text-sm text-slate-400">System policy update</p>
                            </div>
                        </div>

                        <p className="text-slate-300 text-sm leading-relaxed mb-6">
                            Are you sure you want to save these settings? 
                            Applying these changes will immediately affect all monitored devices and may interrupt active user sessions.
                        </p>

                        <div className="flex justify-end gap-3">
                            <button 
                                onClick={() => setIsModalOpen(false)}
                                className="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors text-sm font-medium"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={confirmSave}
                                disabled={saveStatus === 'SAVING'}
                                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-bold shadow-lg shadow-cyan-900/20 flex items-center gap-2"
                            >
                                {saveStatus === 'SAVING' ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Applying...
                                    </>
                                ) : 'Confirm Update'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Settings;