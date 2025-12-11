import React from 'react';
import { LayoutDashboard, Activity, BrainCircuit, Settings, Shield, Users, LogOut, Zap, Keyboard } from 'lucide-react';
import { ViewState, UserProfile } from '../types';

interface SidebarProps {
    currentView: ViewState;
    onChangeView: (view: ViewState) => void;
    currentUser: UserProfile | null;
    onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onChangeView, currentUser, onLogout }) => {
    
    // Base menu items
    const allMenuItems: { id: ViewState; label: string; icon: React.ReactNode; requiredPerm?: string }[] = [
        { id: 'DASHBOARD', label: 'Overview', icon: <LayoutDashboard size={20} /> },
        { id: 'LIVE_MONITOR', label: 'Live Monitor', icon: <Activity size={20} />, requiredPerm: 'READ_LOGS' },
        { id: 'KEYLOGGER', label: 'Keylogger', icon: <Keyboard size={20} />, requiredPerm: 'READ_LOGS' },
        { id: 'AI_ANALYST', label: 'AI Analyst', icon: <BrainCircuit size={20} />, requiredPerm: 'READ_LOGS' },
        { id: 'AUTOMATION', label: 'Auto-Response', icon: <Zap size={20} />, requiredPerm: 'EDIT_SETTINGS' },
        { id: 'USERS', label: 'User Access', icon: <Users size={20} />, requiredPerm: 'MANAGE_USERS' },
        { id: 'SETTINGS', label: 'Policy Control', icon: <Settings size={20} />, requiredPerm: 'EDIT_SETTINGS' },
    ];

    // Filter menu items based on user permissions
    const menuItems = allMenuItems.filter(item => {
        if (!item.requiredPerm) return true; // Always show if no permission required
        return currentUser?.permissions.includes(item.requiredPerm) || currentUser?.role === 'Admin'; 
        // Note: Admin check is a fallback/override
    });

    return (
        <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-screen flex-shrink-0 z-10">
            <div className="p-6 flex items-center gap-3 border-b border-slate-800">
                <div className="w-10 h-10 bg-cyan-500/10 rounded-lg flex items-center justify-center border border-cyan-500/30 text-cyan-400 shadow-neon">
                    <Shield size={24} />
                </div>
                <div>
                    <h1 className="font-bold text-lg tracking-wider text-slate-100">SENTINEL</h1>
                    <p className="text-xs text-cyan-500 font-mono tracking-widest">V.2.1.0</p>
                </div>
            </div>

            {/* User Badge */}
            <div className="px-4 pt-6 pb-2">
                <div className="bg-slate-900 rounded-lg p-3 border border-slate-800 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-cyan-500 border border-slate-700">
                        {currentUser?.name.charAt(0)}
                    </div>
                    <div className="overflow-hidden">
                        <p className="text-sm font-bold text-slate-200 truncate">{currentUser?.name}</p>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wide truncate">{currentUser?.role}</p>
                    </div>
                </div>
            </div>

            <nav className="flex-1 py-4 px-3 space-y-2 overflow-y-auto">
                {menuItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onChangeView(item.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-300 group
                            ${currentView === item.id 
                                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]' 
                                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                            }`}
                    >
                        <span className={`${currentView === item.id ? 'animate-pulse' : ''}`}>
                            {item.icon}
                        </span>
                        <span className="font-medium tracking-wide text-sm">{item.label}</span>
                        {currentView === item.id && (
                            <div className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-neon" />
                        )}
                    </button>
                ))}
            </nav>

            <div className="p-4 border-t border-slate-800 space-y-4">
                 <button 
                    onClick={onLogout}
                    className="w-full flex items-center gap-3 px-4 py-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all text-sm"
                >
                    <LogOut size={18} />
                    Logout
                </button>

                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-ping" />
                        <span className="text-xs font-mono text-green-400">SYSTEM ONLINE</span>
                    </div>
                    <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-cyan-500 w-[85%] relative">
                            <div className="absolute top-0 right-0 w-2 h-full bg-white/50 blur-[2px]" />
                        </div>
                    </div>
                    <div className="flex justify-between mt-1">
                        <span className="text-[10px] text-slate-500">CPU</span>
                        <span className="text-[10px] text-cyan-400 font-mono">34%</span>
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;