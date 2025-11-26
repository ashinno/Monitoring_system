import React, { useState, useEffect } from 'react';
import { Play, Square, Activity, Settings, RefreshCw, Save, Trash2, FolderOpen } from 'lucide-react';
import { startSimulation, stopSimulation, getSimulationStatus, getSimulationProfiles, createSimulationProfile, deleteSimulationProfile } from '../services/api';

const TrafficSimulator: React.FC = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [stats, setStats] = useState({ packetsGenerated: 0, bytesGenerated: 0 });
    const [config, setConfig] = useState({
        trafficType: 'HTTP',
        volume: 'medium',
        pattern: 'steady',
        errorRate: 0.0,
        latency: 0
    });
    const [loading, setLoading] = useState(false);
    
    // Profile State
    const [profiles, setProfiles] = useState<any[]>([]);
    const [profileName, setProfileName] = useState('');
    const [showSaveProfile, setShowSaveProfile] = useState(false);

    const fetchStatus = async () => {
        try {
            const response = await getSimulationStatus();
            if (response.data) {
                setIsRunning(response.data.isRunning);
                if (response.data.stats) {
                    setStats(response.data.stats);
                }
            }
        } catch (error) {
            console.error("Failed to fetch simulation status", error);
        }
    };

    const fetchProfiles = async () => {
        try {
            const response = await getSimulationProfiles();
            setProfiles(response.data);
        } catch (error) {
            console.error("Failed to fetch profiles", error);
        }
    };

    useEffect(() => {
        fetchStatus();
        fetchProfiles();
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    const handleStart = async () => {
        setLoading(true);
        try {
            await startSimulation({
                trafficType: config.trafficType,
                volume: config.volume,
                pattern: config.pattern,
                errorRate: config.errorRate,
                packetSizeRange: [500, 1500],
                latency: config.latency
            });
            setIsRunning(true);
        } catch (error) {
            console.error("Failed to start simulation", error);
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async () => {
        setLoading(true);
        try {
            await stopSimulation();
            setIsRunning(false);
        } catch (error) {
            console.error("Failed to stop simulation", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveProfile = async () => {
        if (!profileName.trim()) return;
        try {
            await createSimulationProfile({
                name: profileName,
                description: `Profile for ${config.trafficType} - ${config.volume}`,
                trafficType: config.trafficType,
                volume: config.volume,
                pattern: config.pattern,
                errorRate: config.errorRate,
                packetSizeRange: [500, 1500],
                latency: config.latency
            });
            setProfileName('');
            setShowSaveProfile(false);
            fetchProfiles();
        } catch (error) {
            console.error("Failed to save profile", error);
            alert("Failed to save profile (name might be duplicate)");
        }
    };

    const handleLoadProfile = (profile: any) => {
        setConfig({
            trafficType: profile.trafficType,
            volume: profile.volume,
            pattern: profile.pattern,
            errorRate: profile.errorRate,
            latency: profile.latency || 0
        });
    };

    const handleDeleteProfile = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!window.confirm("Are you sure you want to delete this profile?")) return;
        try {
            await deleteSimulationProfile(id);
            fetchProfiles();
        } catch (error) {
            console.error("Failed to delete profile", error);
        }
    };

    return (
        <div className="glass-panel p-6 rounded-xl animate-fadeIn mt-6 border border-slate-700/50">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Activity className="text-purple-400" size={20} />
                        Traffic Simulator
                    </h3>
                    <p className="text-slate-400 text-sm mt-1">Generate synthetic network traffic for testing.</p>
                </div>
                <div className="flex items-center gap-2">
                    {isRunning ? (
                        <span className="flex items-center gap-2 text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded border border-green-500/20">
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            RUNNING
                        </span>
                    ) : (
                         <span className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-800 px-2 py-1 rounded border border-slate-700">
                            <span className="w-2 h-2 rounded-full bg-slate-500" />
                            STOPPED
                        </span>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Controls */}
                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs text-slate-400 font-mono mb-2 block">Traffic Type</label>
                            <select 
                                value={config.trafficType}
                                onChange={(e) => setConfig({...config, trafficType: e.target.value})}
                                disabled={isRunning}
                                className="w-full bg-slate-900 border border-slate-700 text-white text-sm rounded p-2 focus:ring-1 focus:ring-purple-500 outline-none"
                            >
                                <option value="HTTP">HTTP (Web)</option>
                                <option value="TCP">TCP (Generic)</option>
                                <option value="UDP">UDP (Stream)</option>
                            </select>
                        </div>
                         <div>
                            <label className="text-xs text-slate-400 font-mono mb-2 block">Volume</label>
                            <select 
                                value={config.volume}
                                onChange={(e) => setConfig({...config, volume: e.target.value})}
                                disabled={isRunning}
                                className="w-full bg-slate-900 border border-slate-700 text-white text-sm rounded p-2 focus:ring-1 focus:ring-purple-500 outline-none"
                            >
                                <option value="low">Low (Background)</option>
                                <option value="medium">Medium (Normal)</option>
                                <option value="high">High (Stress Test)</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs text-slate-400 font-mono mb-2 block">Pattern</label>
                            <select 
                                value={config.pattern}
                                onChange={(e) => setConfig({...config, pattern: e.target.value})}
                                disabled={isRunning}
                                className="w-full bg-slate-900 border border-slate-700 text-white text-sm rounded p-2 focus:ring-1 focus:ring-purple-500 outline-none"
                            >
                                <option value="steady">Steady</option>
                                <option value="bursty">Bursty</option>
                                <option value="random">Random</option>
                            </select>
                        </div>
                         <div>
                            <label className="text-xs text-slate-400 font-mono mb-2 block">Error Rate ({config.errorRate * 100}%)</label>
                            <input 
                                type="range" 
                                min="0" 
                                max="0.5" 
                                step="0.01"
                                value={config.errorRate}
                                onChange={(e) => setConfig({...config, errorRate: parseFloat(e.target.value)})}
                                disabled={isRunning}
                                className="w-full accent-purple-500"
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-400 font-mono mb-2 block">Latency ({config.latency}ms)</label>
                            <input 
                                type="range" 
                                min="0" 
                                max="1000" 
                                step="10"
                                value={config.latency}
                                onChange={(e) => setConfig({...config, latency: parseInt(e.target.value)})}
                                disabled={isRunning}
                                className="w-full accent-purple-500"
                            />
                        </div>
                    </div>

                    <div className="pt-2 flex gap-2">
                        {!isRunning ? (
                            <button 
                                onClick={handleStart}
                                disabled={loading}
                                className="flex-1 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                            >
                                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Play size={18} fill="currentColor" />}
                                Start
                            </button>
                        ) : (
                            <button 
                                onClick={handleStop}
                                disabled={loading}
                                className="flex-1 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                            >
                                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Square size={18} fill="currentColor" />}
                                Stop
                            </button>
                        )}
                        
                        <button 
                            onClick={() => setShowSaveProfile(!showSaveProfile)}
                            disabled={loading || isRunning}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-all border border-slate-700 disabled:opacity-50"
                            title="Save Profile"
                        >
                            <Save size={18} />
                        </button>
                    </div>
                    
                    {/* Save Profile Input */}
                    {showSaveProfile && (
                        <div className="flex gap-2 animate-fadeIn">
                            <input 
                                type="text" 
                                placeholder="Profile Name" 
                                value={profileName}
                                onChange={(e) => setProfileName(e.target.value)}
                                className="flex-1 bg-slate-900 border border-slate-700 text-white text-sm rounded p-2 focus:ring-1 focus:ring-purple-500 outline-none"
                            />
                            <button 
                                onClick={handleSaveProfile}
                                className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-sm"
                            >
                                Save
                            </button>
                        </div>
                    )}
                </div>

                {/* Right Column: Stats & Profiles */}
                <div className="space-y-4">
                    {/* Stats */}
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-800 flex flex-col justify-center">
                        <h4 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                            <Settings size={14} />
                            Session Metrics
                        </h4>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50">
                                <div className="text-xs text-slate-500 font-mono mb-1">Packets Sent</div>
                                <div className="text-xl font-bold text-white font-mono">{(stats?.packetsGenerated || 0).toLocaleString()}</div>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50">
                                <div className="text-xs text-slate-500 font-mono mb-1">Data Generated</div>
                                <div className="text-xl font-bold text-white font-mono">
                                    {((stats?.bytesGenerated || 0) / (1024 * 1024)).toFixed(2)} MB
                                </div>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50 col-span-2">
                                <div className="text-xs text-slate-500 font-mono mb-1">Simulated Status</div>
                                <div className="text-sm text-slate-300">
                                    Generating <span className="text-purple-400 font-bold">{config.volume}</span> volume 
                                    <span className="text-purple-400 font-bold"> {config.trafficType}</span> traffic 
                                    with <span className="text-purple-400 font-bold">{config.pattern}</span> pattern.
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Profiles List */}
                    {profiles.length > 0 && (
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-800">
                            <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                                <FolderOpen size={14} />
                                Saved Profiles
                            </h4>
                            <div className="space-y-2 max-h-40 overflow-y-auto pr-1 custom-scrollbar">
                                {profiles.map(profile => (
                                    <div key={profile.id} className="flex items-center justify-between p-2 bg-slate-800/50 rounded border border-slate-700/30 hover:border-purple-500/50 transition-colors group">
                                        <div className="cursor-pointer flex-1" onClick={() => handleLoadProfile(profile)}>
                                            <div className="text-sm font-medium text-slate-200 group-hover:text-purple-300">{profile.name}</div>
                                            <div className="text-xs text-slate-500 font-mono">{profile.trafficType} • {profile.volume} • {profile.pattern}</div>
                                        </div>
                                        <button 
                                            onClick={(e) => handleDeleteProfile(profile.id, e)}
                                            className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TrafficSimulator;
