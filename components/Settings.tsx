import React, { useState, useEffect } from 'react';
import { Shield, Lock, Eye, Bell, Save, AlertTriangle, X, CheckCircle, Plus, Trash2, Mail, MessageSquare, Server, Terminal, Play, Square } from 'lucide-react';
import API, { getAgentStatus, startAgent, stopAgent } from '../services/api';

const Settings: React.FC = () => {
    const [settings, setSettings] = useState({
        blockGambling: true,
        blockSocialMedia: false,
        enforceSafeSearch: true,
        screenTimeLimit: true,
        alertOnKeywords: true,
        captureScreenshots: false,
        keywords: [] as string[],
        emailNotifications: false,
        notificationEmail: "",
        webhookUrl: "",
        quietHoursStart: "",
        quietHoursEnd: "",
        // Advanced Notifications
        smtpServer: "",
        smtpPort: 587,
        smtpUsername: "",
        smtpPassword: "",
        smsNotifications: false,
        twilioAccountSid: "",
        twilioAuthToken: "",
        twilioFromNumber: "",
        twilioToNumber: ""
    });
    const [newKeyword, setNewKeyword] = useState("");
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'IDLE' | 'SAVING' | 'SAVED'>('IDLE');
    const [testResult, setTestResult] = useState<string | null>(null);
    
    // Agent State
    const [agentStatus, setAgentStatus] = useState<{is_running: boolean, pid: number | null}>({ is_running: false, pid: null });
    const [agentLoading, setAgentLoading] = useState(false);

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
        checkAgentStatus();
        
        // Poll agent status
        const interval = setInterval(checkAgentStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const checkAgentStatus = async () => {
        try {
            const res = await getAgentStatus();
            setAgentStatus(res.data);
        } catch (e) {
            console.error("Failed to check agent status", e);
        }
    };

    const handleStartAgent = async () => {
        setAgentLoading(true);
        try {
            await startAgent();
            await checkAgentStatus();
        } catch (e) {
            console.error("Failed to start agent", e);
        } finally {
            setAgentLoading(false);
        }
    };

    const handleStopAgent = async () => {
        setAgentLoading(true);
        try {
            await stopAgent();
            await checkAgentStatus();
        } catch (e) {
            console.error("Failed to stop agent", e);
        } finally {
            setAgentLoading(false);
        }
    };

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
    
    const handleTestNotification = async () => {
        try {
            // Save first to ensure backend tests latest config
            await API.put('/settings', settings);
            const response = await API.post('/notifications/test');
            setTestResult(JSON.stringify(response.data, null, 2));
            setTimeout(() => setTestResult(null), 5000);
        } catch (error) {
            console.error("Test failed", error);
            setTestResult("Test failed: " + String(error));
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn relative pb-20">
            
            {/* Success Feedback Banner */}
            {saveStatus === 'SAVED' && (
                <div className="absolute -top-12 left-0 right-0 z-20 animate-slideDown">
                    <div className="bg-green-500/10 backdrop-blur-md border border-green-500/40 text-green-400 p-3 rounded-lg flex items-center justify-center gap-3 shadow-[0_0_15px_rgba(34,197,94,0.2)]">
                        <CheckCircle size={20} />
                        <span className="font-semibold">Settings saved successfully! System policies have been updated.</span>
                    </div>
                </div>
            )}
            
            {testResult && (
                 <div className="fixed bottom-10 right-10 z-50 animate-slideUp max-w-md w-full">
                    <div className="bg-slate-800 border border-slate-600 p-4 rounded-xl shadow-2xl">
                        <div className="flex justify-between items-center mb-2">
                             <h4 className="text-white font-semibold">Notification Test Result</h4>
                             <button onClick={() => setTestResult(null)}><X size={16} className="text-slate-400" /></button>
                        </div>
                        <pre className="text-xs text-green-400 overflow-auto max-h-40 bg-black/30 p-2 rounded">
                            {testResult}
                        </pre>
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

                {/* Agent Control Panel */}
                <div className="glass-panel p-6 rounded-xl border-t-4 border-t-emerald-500 md:col-span-2">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-slate-900 rounded border border-slate-800 text-emerald-400">
                                <Terminal size={20} />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Monitoring Agent</h3>
                                <p className="text-slate-400 text-xs">Manage local data collection agent</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${agentStatus.is_running ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                                <span className={`w-2 h-2 rounded-full ${agentStatus.is_running ? 'bg-emerald-500 animate-pulse' : 'bg-slate-500'}`} />
                                {agentStatus.is_running ? `Running (PID: ${agentStatus.pid})` : 'Stopped'}
                            </span>
                        </div>
                    </div>

                    <div className="bg-slate-900/40 p-4 rounded-lg border border-slate-800 flex items-center justify-between">
                        <div>
                            <p className="text-slate-200 font-medium">Agent Status Control</p>
                            <p className="text-slate-500 text-xs mt-1">
                                The agent captures keystrokes (encrypted) and system metrics. 
                                <br/>Ensure "Input Monitoring" permission is granted on macOS.
                            </p>
                        </div>
                        <div className="flex gap-3">
                            {!agentStatus.is_running ? (
                                <button 
                                    onClick={handleStartAgent}
                                    disabled={agentLoading}
                                    className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-all shadow-lg shadow-emerald-900/20"
                                >
                                    <Play size={16} fill="currentColor" />
                                    {agentLoading ? "Starting..." : "Start Agent"}
                                </button>
                            ) : (
                                <button 
                                    onClick={handleStopAgent}
                                    disabled={agentLoading}
                                    className="flex items-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-all shadow-lg shadow-red-900/20"
                                >
                                    <Square size={16} fill="currentColor" />
                                    {agentLoading ? "Stopping..." : "Stop Agent"}
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Notifications */}
                <div className="glass-panel p-6 rounded-xl border-t-4 border-t-yellow-500 md:col-span-2">
                    <div className="flex items-center justify-between mb-6">
                         <div className="flex items-center gap-3">
                            <div className="p-2 bg-slate-900 rounded border border-slate-800 text-yellow-400">
                                <Bell size={20} />
                            </div>
                            <h3 className="text-lg font-semibold text-white">Alert Configuration</h3>
                        </div>
                        <button 
                            onClick={handleTestNotification}
                            className="text-xs bg-slate-700 hover:bg-slate-600 text-white px-3 py-1 rounded border border-slate-600 transition-colors"
                        >
                            Test Notifications
                        </button>
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
                        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 mt-2 mb-6">
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

                    <div className="mt-6 space-y-6">
                        {/* Email Settings */}
                        <div className="space-y-3">
                             <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg">
                                <div className="flex items-center gap-2">
                                    <Mail size={16} className="text-slate-400"/>
                                    <div>
                                        <p className="text-slate-200 font-medium">Email Notifications</p>
                                        <p className="text-slate-500 text-xs">Receive alerts via SMTP</p>
                                    </div>
                                </div>
                                 <button 
                                    onClick={() => toggle('emailNotifications')}
                                    className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.emailNotifications ? 'bg-yellow-600' : 'bg-slate-700'}`}
                                >
                                    <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.emailNotifications ? 'translate-x-6' : 'translate-x-0'}`} />
                                </button>
                            </div>
                            
                            {settings.emailNotifications && (
                                <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="col-span-2">
                                        <label className="text-slate-400 text-xs mb-1 block">Notification Email</label>
                                        <input 
                                            type="email" 
                                            value={settings.notificationEmail || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, notificationEmail: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                            placeholder="admin@example.com"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-400 text-xs mb-1 block">SMTP Server</label>
                                        <input 
                                            type="text" 
                                            value={settings.smtpServer || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, smtpServer: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                            placeholder="smtp.gmail.com"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-400 text-xs mb-1 block">SMTP Port</label>
                                        <input 
                                            type="number" 
                                            value={settings.smtpPort || 587}
                                            onChange={(e) => setSettings(prev => ({ ...prev, smtpPort: parseInt(e.target.value) }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                            placeholder="587"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-400 text-xs mb-1 block">SMTP Username</label>
                                        <input 
                                            type="text" 
                                            value={settings.smtpUsername || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, smtpUsername: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-400 text-xs mb-1 block">SMTP Password</label>
                                        <input 
                                            type="password" 
                                            value={settings.smtpPassword || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, smtpPassword: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* SMS Settings */}
                        <div className="space-y-3">
                             <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg">
                                <div className="flex items-center gap-2">
                                    <MessageSquare size={16} className="text-slate-400"/>
                                    <div>
                                        <p className="text-slate-200 font-medium">SMS Notifications</p>
                                        <p className="text-slate-500 text-xs">Receive alerts via Twilio</p>
                                    </div>
                                </div>
                                 <button 
                                    onClick={() => toggle('smsNotifications')}
                                    className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${settings.smsNotifications ? 'bg-yellow-600' : 'bg-slate-700'}`}
                                >
                                    <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${settings.smsNotifications ? 'translate-x-6' : 'translate-x-0'}`} />
                                </button>
                            </div>
                            
                            {settings.smsNotifications && (
                                <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="col-span-2">
                                        <label className="text-slate-400 text-xs mb-1 block">Twilio Account SID</label>
                                        <input 
                                            type="text" 
                                            value={settings.twilioAccountSid || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, twilioAccountSid: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                        />
                                    </div>
                                    <div className="col-span-2">
                                        <label className="text-slate-400 text-xs mb-1 block">Twilio Auth Token</label>
                                        <input 
                                            type="password" 
                                            value={settings.twilioAuthToken || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, twilioAuthToken: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-400 text-xs mb-1 block">From Number</label>
                                        <input 
                                            type="text" 
                                            value={settings.twilioFromNumber || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, twilioFromNumber: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                            placeholder="+1234567890"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-400 text-xs mb-1 block">To Number</label>
                                        <input 
                                            type="text" 
                                            value={settings.twilioToNumber || ""}
                                            onChange={(e) => setSettings(prev => ({ ...prev, twilioToNumber: e.target.value }))}
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                            placeholder="+1987654321"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Webhook */}
                        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
                            <div className="flex items-center gap-2 mb-2">
                                <Server size={16} className="text-slate-400"/>
                                <label className="text-slate-400 text-xs block">Webhook URL (Slack/Discord)</label>
                            </div>
                            <input 
                                type="text" 
                                value={settings.webhookUrl || ""}
                                onChange={(e) => setSettings(prev => ({ ...prev, webhookUrl: e.target.value }))}
                                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                placeholder="https://hooks.slack.com/services/..."
                            />
                        </div>

                        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-800">
                            <p className="text-slate-200 font-medium mb-2">Quiet Hours</p>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-slate-500 text-xs mb-1 block">Start Time</label>
                                    <input 
                                        type="time" 
                                        value={settings.quietHoursStart || ""}
                                        onChange={(e) => setSettings(prev => ({ ...prev, quietHoursStart: e.target.value }))}
                                        className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-slate-500 text-xs mb-1 block">End Time</label>
                                    <input 
                                        type="time" 
                                        value={settings.quietHoursEnd || ""}
                                        onChange={(e) => setSettings(prev => ({ ...prev, quietHoursEnd: e.target.value }))}
                                        className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-yellow-500 outline-none"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

             {/* Save Button */}
             <div className="fixed bottom-6 right-6 z-30">
                <button 
                    onClick={handleSaveClick}
                    className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white px-6 py-3 rounded-full shadow-lg shadow-cyan-500/20 flex items-center gap-2 font-semibold transition-all transform hover:scale-105"
                >
                    <Save size={20} />
                    Save Changes
                </button>
            </div>

            {/* Confirmation Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl max-w-sm w-full shadow-2xl">
                        <div className="flex flex-col items-center text-center mb-6">
                            <div className="w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center mb-4 text-yellow-500">
                                <AlertTriangle size={32} />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">Confirm Changes</h3>
                            <p className="text-slate-400 text-sm">
                                Are you sure you want to update system policies? New settings will be enforced immediately across all monitored devices.
                            </p>
                        </div>
                        
                        <div className="flex gap-3">
                            <button 
                                onClick={() => setIsModalOpen(false)}
                                className="flex-1 px-4 py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={confirmSave}
                                disabled={saveStatus === 'SAVING'}
                                className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors"
                            >
                                {saveStatus === 'SAVING' ? 'Saving...' : 'Confirm'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Settings;
