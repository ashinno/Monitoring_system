import React, { useEffect, useState } from 'react';
import { Play, Square, Activity, RefreshCw, Network, Timer, AlertTriangle } from 'lucide-react';
import { AttackScenario, getInterceptionInterfaces, getInterceptionStatus, simulateAttackBurst, startInterception, stopInterception } from '../services/api';

type InterceptionStats = {
    packetsIntercepted: number;
    bytesIntercepted: number;
    errors: number;
};

const defaultStats: InterceptionStats = {
    packetsIntercepted: 0,
    bytesIntercepted: 0,
    errors: 0,
};

const attackOptions: { id: AttackScenario; label: string; burst: number }[] = [
    { id: 'ddos', label: 'Simulate DDoS', burst: 40 },
    { id: 'port_scan', label: 'Simulate Port Scan', burst: 60 },
    { id: 'brute_force', label: 'Simulate Brute Force', burst: 45 },
    { id: 'data_exfiltration', label: 'Simulate Exfiltration', burst: 30 },
];

const TrafficInterceptor: React.FC = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [loading, setLoading] = useState(false);
    const [interfaces, setInterfaces] = useState<string[]>([]);
    const [stats, setStats] = useState<InterceptionStats>(defaultStats);
    const [attackLoading, setAttackLoading] = useState<AttackScenario | null>(null);
    const [attackResult, setAttackResult] = useState('');
    const [config, setConfig] = useState({
        interface: '',
        protocols: ['TCP', 'UDP'],
        includeLoopback: false,
        pollIntervalMs: 1000,
    });

    const fetchStatus = async () => {
        try {
            const response = await getInterceptionStatus();
            if (!response.data) {
                return;
            }

            const status = response.data;
            setIsRunning(status.isRunning);

            if (status.config) {
                setConfig((prev) => ({
                    interface: status.config.interface || '',
                    protocols: status.config.protocols?.length ? status.config.protocols : prev.protocols,
                    includeLoopback: !!status.config.includeLoopback,
                    pollIntervalMs: status.config.pollIntervalMs || prev.pollIntervalMs,
                }));
            }

            if (status.stats) {
                setStats({
                    packetsIntercepted: status.stats.packetsIntercepted || 0,
                    bytesIntercepted: status.stats.bytesIntercepted || 0,
                    errors: status.stats.errors || 0,
                });
            }
        } catch (error) {
            console.error('Failed to fetch interception status', error);
        }
    };

    const fetchInterfaces = async () => {
        try {
            const response = await getInterceptionInterfaces();
            setInterfaces(response.data || []);
        } catch (error) {
            console.error('Failed to fetch interfaces', error);
        }
    };

    useEffect(() => {
        fetchInterfaces();
        fetchStatus();

        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    const toggleProtocol = (protocol: 'TCP' | 'UDP') => {
        setConfig((prev) => {
            const hasProtocol = prev.protocols.includes(protocol);
            const updated = hasProtocol
                ? prev.protocols.filter((p) => p !== protocol)
                : [...prev.protocols, protocol];

            return {
                ...prev,
                protocols: updated.length ? updated : [protocol],
            };
        });
    };

    const handleStart = async () => {
        setLoading(true);
        try {
            await startInterception({
                interface: config.interface || undefined,
                protocols: config.protocols,
                includeLoopback: config.includeLoopback,
                pollIntervalMs: config.pollIntervalMs,
            });
            setIsRunning(true);
            fetchStatus();
        } catch (error: any) {
            const message = error?.response?.data?.detail || 'Failed to start interception';
            console.error(message, error);
            alert(message);
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async () => {
        setLoading(true);
        try {
            await stopInterception();
            setIsRunning(false);
            fetchStatus();
        } catch (error) {
            console.error('Failed to stop interception', error);
        } finally {
            setLoading(false);
        }
    };

    const runAttackSimulation = async (scenario: AttackScenario, burst: number) => {
        setAttackLoading(scenario);
        setAttackResult('');
        try {
            const result = await simulateAttackBurst(scenario, burst);
            setAttackResult(`${scenario.replace('_', ' ').toUpperCase()} injected ${result.successful}/${result.attempted} events`);
        } catch (error) {
            console.error('Failed to simulate attack', error);
            setAttackResult(`Failed to run ${scenario.replace('_', ' ').toUpperCase()} simulation`);
        } finally {
            setAttackLoading(null);
        }
    };

    return (
        <div className="glass-panel p-6 rounded-xl animate-fadeIn mt-6 border border-slate-700/50">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Activity className="text-purple-400" size={20} />
                        Real Traffic Interceptor
                    </h3>
                    <p className="text-slate-400 text-sm mt-1">Capture live host traffic and stream it into analytics.</p>
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
                <div className="space-y-4">
                    <div>
                        <label className="text-xs text-slate-400 font-mono mb-2 block">Network Interface</label>
                        <select
                            value={config.interface}
                            onChange={(e) => setConfig({ ...config, interface: e.target.value })}
                            disabled={isRunning}
                            className="w-full bg-slate-900 border border-slate-700 text-white text-sm rounded p-2 focus:ring-1 focus:ring-purple-500 outline-none"
                        >
                            <option value="">All Interfaces</option>
                            {interfaces.map((iface) => (
                                <option key={iface} value={iface}>
                                    {iface}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="text-xs text-slate-400 font-mono mb-2 block">Protocols</label>
                        <div className="grid grid-cols-2 gap-2">
                            {(['TCP', 'UDP'] as const).map((protocol) => {
                                const enabled = config.protocols.includes(protocol);
                                return (
                                    <button
                                        key={protocol}
                                        onClick={() => toggleProtocol(protocol)}
                                        disabled={isRunning}
                                        className={`px-2 py-2 text-xs font-medium rounded border transition-all ${
                                            enabled
                                                ? 'bg-purple-500/20 border-purple-500 text-purple-300'
                                                : 'bg-slate-900 border-slate-700 text-slate-400 hover:bg-slate-800'
                                        }`}
                                    >
                                        {protocol}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <div className="flex items-center justify-between bg-slate-900/50 rounded border border-slate-800 p-3">
                        <span className="text-xs text-slate-300 font-mono">Include Loopback (127.0.0.1)</span>
                        <button
                            onClick={() => setConfig({ ...config, includeLoopback: !config.includeLoopback })}
                            disabled={isRunning}
                            className={`px-3 py-1 text-xs rounded border transition-all ${
                                config.includeLoopback
                                    ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300'
                                    : 'bg-slate-900 border-slate-700 text-slate-400'
                            }`}
                        >
                            {config.includeLoopback ? 'ON' : 'OFF'}
                        </button>
                    </div>

                    <div>
                        <label className="text-xs text-slate-400 font-mono mb-2 block">Polling Interval ({config.pollIntervalMs}ms)</label>
                        <input
                            type="range"
                            min="200"
                            max="5000"
                            step="100"
                            value={config.pollIntervalMs}
                            onChange={(e) => setConfig({ ...config, pollIntervalMs: parseInt(e.target.value, 10) })}
                            disabled={isRunning}
                            className="w-full accent-purple-500"
                        />
                    </div>

                    <div className="pt-2 flex gap-2">
                        {!isRunning ? (
                            <button
                                onClick={handleStart}
                                disabled={loading}
                                className="flex-1 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                            >
                                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Play size={18} fill="currentColor" />}
                                Start Interception
                            </button>
                        ) : (
                            <button
                                onClick={handleStop}
                                disabled={loading}
                                className="flex-1 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                            >
                                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Square size={18} fill="currentColor" />}
                                Stop Interception
                            </button>
                        )}
                    </div>

                    <div className="bg-slate-900/50 rounded border border-slate-800 p-3 space-y-3">
                        <div className="text-xs text-slate-300 font-mono">Attack Simulation</div>
                        <div className="grid grid-cols-2 gap-2">
                            {attackOptions.map((option) => (
                                <button
                                    key={option.id}
                                    onClick={() => runAttackSimulation(option.id, option.burst)}
                                    disabled={!!attackLoading}
                                    className={`px-2 py-2 text-xs font-medium rounded border transition-all ${
                                        attackLoading === option.id
                                            ? 'bg-red-500/30 border-red-500 text-red-200'
                                            : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800'
                                    } disabled:opacity-50`}
                                >
                                    {attackLoading === option.id ? 'Injecting...' : option.label}
                                </button>
                            ))}
                        </div>
                        {attackResult && (
                            <div className="text-xs font-mono text-cyan-300">{attackResult}</div>
                        )}
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-800 flex flex-col justify-center">
                        <h4 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                            <Network size={14} />
                            Interception Metrics
                        </h4>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50">
                                <div className="text-xs text-slate-500 font-mono mb-1">Flows Captured</div>
                                <div className="text-xl font-bold text-white font-mono">{stats.packetsIntercepted.toLocaleString()}</div>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50">
                                <div className="text-xs text-slate-500 font-mono mb-1">Traffic Volume</div>
                                <div className="text-xl font-bold text-white font-mono">
                                    {(stats.bytesIntercepted / (1024 * 1024)).toFixed(2)} MB
                                </div>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50">
                                <div className="text-xs text-slate-500 font-mono mb-1">Capture Errors</div>
                                <div className="text-xl font-bold text-white font-mono">{stats.errors.toLocaleString()}</div>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50">
                                <div className="text-xs text-slate-500 font-mono mb-1">Poll Interval</div>
                                <div className="text-xl font-bold text-white font-mono">{config.pollIntervalMs}ms</div>
                            </div>
                            <div className="p-3 bg-slate-800/50 rounded border border-slate-700/50 col-span-2">
                                <div className="text-xs text-slate-500 font-mono mb-1 flex items-center gap-1">
                                    <Timer size={12} />
                                    Capture Scope
                                </div>
                                <div className="text-sm text-slate-300">
                                    {config.interface ? (
                                        <>Interface <span className="text-purple-400 font-bold">{config.interface}</span></>
                                    ) : (
                                        <>Monitoring <span className="text-purple-400 font-bold">all interfaces</span></>
                                    )}
                                    {' • '}
                                    Protocols <span className="text-purple-400 font-bold">{config.protocols.join(', ')}</span>
                                    {!config.includeLoopback && (
                                        <>
                                            {' • '}
                                            <span className="inline-flex items-center gap-1 text-amber-400">
                                                <AlertTriangle size={12} />
                                                loopback excluded
                                            </span>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TrafficInterceptor;
