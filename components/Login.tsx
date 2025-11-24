import React, { useState } from 'react';
import { Shield, Lock, User, ArrowRight, AlertTriangle } from 'lucide-react';

interface LoginProps {
    onLogin: (id: string, pass: string) => void;
    error?: string;
}

const Login: React.FC<LoginProps> = ({ onLogin, error }) => {
    const [userId, setUserId] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        // Simulate network delay for effect
        setTimeout(() => {
            onLogin(userId, password);
            setIsLoading(false);
        }, 800);
    };

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-cyan-900/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-900/10 rounded-full blur-[120px]" />
                <div className="absolute top-0 left-0 w-full h-full opacity-[0.05]" style={{
                    backgroundImage: `linear-gradient(#1e293b 1px, transparent 1px), linear-gradient(to right, #1e293b 1px, transparent 1px)`,
                    backgroundSize: '40px 40px'
                }} />
            </div>

            <div className="w-full max-w-md z-10 p-6">
                <div className="glass-panel border border-slate-700/50 p-8 rounded-2xl shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-purple-500 to-cyan-500 animate-pulse" />
                    
                    <div className="flex flex-col items-center mb-8">
                        <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center border border-cyan-500/30 text-cyan-400 shadow-neon mb-4">
                            <Shield size={32} />
                        </div>
                        <h1 className="text-2xl font-bold text-white tracking-widest">SENTINEL ACCESS</h1>
                        <p className="text-slate-500 text-xs font-mono mt-2">SECURE GATEWAY V.2.1.0</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 flex items-center gap-3 text-red-400 text-sm animate-fadeIn">
                                <AlertTriangle size={16} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-xs text-slate-400 font-mono uppercase">Identity Key / User ID</label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                                <input 
                                    type="text" 
                                    value={userId}
                                    onChange={(e) => setUserId(e.target.value)}
                                    className="w-full bg-slate-900/80 border border-slate-700 rounded-lg py-3 pl-10 pr-4 text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 transition-all"
                                    placeholder="Enter User ID"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs text-slate-400 font-mono uppercase">Passcode</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                                <input 
                                    type="password" 
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-slate-900/80 border border-slate-700 rounded-lg py-3 pl-10 pr-4 text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button 
                            type="submit" 
                            disabled={isLoading}
                            className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 rounded-lg shadow-neon flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    AUTHENTICATE
                                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-slate-800 text-center">
                        <p className="text-[10px] text-slate-600 font-mono">
                            UNAUTHORIZED ACCESS ATTEMPTS ARE MONITORED AND LOGGED.
                            <br />SESSION ID: {Math.random().toString(36).substr(2, 8).toUpperCase()}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;