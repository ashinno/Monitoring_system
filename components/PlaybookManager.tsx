import React, { useState } from 'react';
import { Zap, Plus, Trash2, Play, CheckSquare, XSquare, AlertTriangle } from 'lucide-react';
import { PlaybookRule, RiskLevel, ActivityType } from '../types';

interface PlaybookManagerProps {
    rules: PlaybookRule[];
    onAddRule: (rule: PlaybookRule) => void;
    onDeleteRule: (id: string) => void;
    onToggleRule: (id: string) => void;
}

const PlaybookManager: React.FC<PlaybookManagerProps> = ({ rules, onAddRule, onDeleteRule, onToggleRule }) => {
    const [isCreating, setIsCreating] = useState(false);
    const [newRule, setNewRule] = useState<Partial<PlaybookRule>>({
        trigger: { field: 'riskLevel', operator: 'equals', value: 'CRITICAL' },
        action: { type: 'LOCK_USER' }
    });
    const [name, setName] = useState('');

    const handleSave = () => {
        if (!name) return;
        const rule: PlaybookRule = {
            id: Math.random().toString(36).substr(2, 9),
            name: name,
            isActive: true,
            trigger: newRule.trigger as any,
            action: newRule.action as any
        };
        onAddRule(rule);
        setIsCreating(false);
        setName('');
    };

    return (
        <div className="space-y-6 animate-fadeIn">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                        <Zap className="text-yellow-400" />
                        SOAR Automation
                    </h2>
                    <p className="text-slate-400 mt-1">Configure automated response playbooks for immediate threat mitigation.</p>
                </div>
                <button 
                    onClick={() => setIsCreating(true)}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-all shadow-neon"
                >
                    <Plus size={18} />
                    Create Playbook
                </button>
            </div>

            {/* Active Rules Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {rules.map(rule => (
                    <div key={rule.id} className={`glass-panel p-6 rounded-xl border-l-4 transition-all hover:translate-x-1 ${rule.isActive ? 'border-l-green-500 bg-slate-900/50' : 'border-l-slate-600 opacity-60'}`}>
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-lg font-bold text-white">{rule.name}</h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase ${rule.isActive ? 'bg-green-500/20 text-green-400' : 'bg-slate-700 text-slate-400'}`}>
                                        {rule.isActive ? 'Active' : 'Disabled'}
                                    </span>
                                    <span className="text-slate-500 text-xs">ID: {rule.id}</span>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button 
                                    onClick={() => onToggleRule(rule.id)}
                                    className={`p-2 rounded-lg transition-colors ${rule.isActive ? 'text-green-400 hover:bg-green-500/10' : 'text-slate-500 hover:bg-slate-800'}`}
                                >
                                    {rule.isActive ? <CheckSquare size={18} /> : <XSquare size={18} />}
                                </button>
                                <button 
                                    onClick={() => onDeleteRule(rule.id)}
                                    className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>

                        {/* Logic Visualizer */}
                        <div className="bg-slate-950 rounded-lg p-3 font-mono text-sm border border-slate-800 relative">
                            <div className="absolute top-1/2 left-0 -translate-x-1/2 w-3 h-3 bg-slate-800 rounded-full border border-slate-600" />
                            <div className="flex items-center gap-2 text-cyan-400">
                                <span className="text-purple-400">IF</span> 
                                <span className="bg-slate-900 px-1 rounded border border-slate-700">{rule.trigger.field}</span>
                                <span className="text-slate-500">{rule.trigger.operator}</span>
                                <span className="text-yellow-400">"{rule.trigger.value}"</span>
                            </div>
                            <div className="h-4 border-l border-slate-700 ml-1.5 my-1" />
                            <div className="flex items-center gap-2 text-green-400">
                                <span className="text-purple-400">THEN</span>
                                <span className="flex items-center gap-1 font-bold">
                                    <Play size={12} /> {rule.action.type.replace('_', ' ')}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Creation Modal */}
            {isCreating && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setIsCreating(false)} />
                    
                    <div className="relative bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-lg w-full shadow-2xl animate-slideDown">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                            <Zap className="text-cyan-400" />
                            Configure Response Logic
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs text-slate-400 mb-1">Playbook Name</label>
                                <input 
                                    type="text" 
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-cyan-500 outline-none"
                                    placeholder="e.g., Auto-Lock on Critical Threat"
                                    value={name}
                                    onChange={e => setName(e.target.value)}
                                />
                            </div>

                            <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                                <h4 className="text-sm font-bold text-purple-400 mb-3">TRIGGER CONDITION</h4>
                                <div className="grid grid-cols-3 gap-2">
                                    <select 
                                        className="bg-slate-900 text-slate-200 text-sm p-2 rounded border border-slate-700"
                                        value={newRule.trigger?.field}
                                        onChange={e => setNewRule({...newRule, trigger: {...newRule.trigger!, field: e.target.value as any}})}
                                    >
                                        <option value="riskLevel">Risk Level</option>
                                        <option value="activityType">Activity Type</option>
                                        <option value="description">Description Log</option>
                                    </select>
                                    <select 
                                        className="bg-slate-900 text-slate-200 text-sm p-2 rounded border border-slate-700"
                                        value={newRule.trigger?.operator}
                                        onChange={e => setNewRule({...newRule, trigger: {...newRule.trigger!, operator: e.target.value as any}})}
                                    >
                                        <option value="equals">Equals</option>
                                        <option value="contains">Contains</option>
                                    </select>
                                    <select 
                                        className="bg-slate-900 text-slate-200 text-sm p-2 rounded border border-slate-700"
                                        value={newRule.trigger?.value}
                                        onChange={e => setNewRule({...newRule, trigger: {...newRule.trigger!, value: e.target.value}})}
                                    >
                                        {newRule.trigger?.field === 'riskLevel' ? (
                                            <>
                                                <option value="LOW">LOW</option>
                                                <option value="MEDIUM">MEDIUM</option>
                                                <option value="HIGH">HIGH</option>
                                                <option value="CRITICAL">CRITICAL</option>
                                            </>
                                        ) : (
                                            <>
                                                <option value="WEB">WEB</option>
                                                <option value="NETWORK">NETWORK</option>
                                                <option value="SYSTEM">SYSTEM</option>
                                            </>
                                        )}
                                    </select>
                                </div>
                            </div>

                            <div className="flex justify-center">
                                <div className="h-6 w-px bg-slate-600" />
                            </div>

                            <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                                <h4 className="text-sm font-bold text-green-400 mb-3">EXECUTE ACTION</h4>
                                <select 
                                    className="w-full bg-slate-900 text-slate-200 text-sm p-2 rounded border border-slate-700"
                                    value={newRule.action?.type}
                                    onChange={e => setNewRule({...newRule, action: {type: e.target.value as any}})}
                                >
                                    <option value="LOCK_USER">Lock User Account (Prevents Login)</option>
                                    <option value="QUARANTINE_USER">Quarantine User (Restricted Access)</option>
                                    <option value="ALERT_ADMIN">Generate High Priority Alert</option>
                                </select>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 mt-8">
                            <button 
                                onClick={() => setIsCreating(false)}
                                className="px-4 py-2 rounded-lg text-slate-400 hover:text-white text-sm"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={handleSave}
                                disabled={!name}
                                className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg font-bold shadow-neon disabled:opacity-50"
                            >
                                Activate Playbook
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PlaybookManager;