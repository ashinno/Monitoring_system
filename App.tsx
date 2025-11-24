import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import ActivityLog from './components/ActivityLog';
import AIAnalyst from './components/AIAnalyst';
import Settings from './components/Settings';
import UserManagement from './components/UserManagement';
import PlaybookManager from './components/PlaybookManager';
import Login from './components/Login';
import { ViewState, LogEntry, UserProfile, ActivityType, RiskLevel, PlaybookRule } from './types';
import { MOCK_LOGS } from './constants';
import { Lock } from 'lucide-react';

const App: React.FC = () => {
    // Auth State
    const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
    const [loginError, setLoginError] = useState('');

    const [currentView, setCurrentView] = useState<ViewState>('DASHBOARD');
    
    // Centralized Data State
    const [logs, setLogs] = useState<LogEntry[]>(MOCK_LOGS);
    const [users, setUsers] = useState<UserProfile[]>([]);
    const [playbooks, setPlaybooks] = useState<PlaybookRule[]>([]);

    // Initialize Users & Rules
    useEffect(() => {
        const storedUsers = localStorage.getItem('sentinel_users');
        const storedRules = localStorage.getItem('sentinel_playbooks');
        
        if (storedUsers) {
            setUsers(JSON.parse(storedUsers));
        } else {
            // Default Initial Users
            const defaults: UserProfile[] = [
                { 
                    id: 'admin', 
                    name: 'Admin User', 
                    role: 'Administrator', 
                    clearanceLevel: 'ADMIN', 
                    status: 'ACTIVE', 
                    permissions: ['READ_LOGS', 'EDIT_SETTINGS', 'MANAGE_USERS', 'EXPORT_DATA'],
                    password: 'admin' 
                },
                { 
                    id: 'analyst', 
                    name: 'Alice Williams', 
                    role: 'Security Analyst', 
                    clearanceLevel: 'L2', 
                    status: 'ACTIVE', 
                    permissions: ['READ_LOGS', 'EXPORT_DATA'],
                    password: 'password'
                }
            ];
            setUsers(defaults);
            localStorage.setItem('sentinel_users', JSON.stringify(defaults));
        }

        if (storedRules) {
            setPlaybooks(JSON.parse(storedRules));
        } else {
            const defaultRules: PlaybookRule[] = [
                {
                    id: 'rule-1',
                    name: 'Critical Threat Lockout',
                    isActive: true,
                    trigger: { field: 'riskLevel', operator: 'equals', value: 'CRITICAL' },
                    action: { type: 'LOCK_USER' }
                }
            ];
            setPlaybooks(defaultRules);
            localStorage.setItem('sentinel_playbooks', JSON.stringify(defaultRules));
        }
    }, []);

    const handleLogin = (id: string, pass: string) => {
        const user = users.find(u => (u.id === id || u.name === id) && u.password === pass);
        
        if (user) {
            if (user.status !== 'ACTIVE') {
                setLoginError(`Account is ${user.status}. Contact Administrator.`);
                return;
            }
            setCurrentUser(user);
            setLoginError('');
            setCurrentView('DASHBOARD');
            addLogEntry(ActivityType.SYSTEM, 'User Login', `Successful login by ${user.name}`);
        } else {
            setLoginError('Invalid credentials.');
        }
    };

    const handleLogout = () => {
        if (currentUser) {
            addLogEntry(ActivityType.SYSTEM, 'User Logout', `${currentUser.name} logged out.`);
        }
        setCurrentUser(null);
        setCurrentView('DASHBOARD');
    };

    // RULE ENGINE CORE
    const executePlaybooks = (log: LogEntry) => {
        playbooks.forEach(rule => {
            if (!rule.isActive) return;

            let isMatch = false;
            // Check Trigger
            const fieldVal = log[rule.trigger.field as keyof LogEntry]?.toString().toUpperCase();
            const triggerVal = rule.trigger.value.toUpperCase();

            if (rule.trigger.operator === 'equals') {
                isMatch = fieldVal === triggerVal;
            } else if (rule.trigger.operator === 'contains') {
                isMatch = fieldVal?.includes(triggerVal) || false;
            }

            if (isMatch) {
                // Execute Action
                if (rule.action.type === 'LOCK_USER' || rule.action.type === 'QUARANTINE_USER') {
                    const status = rule.action.type === 'LOCK_USER' ? 'LOCKED' : 'QUARANTINED';
                    setUsers(prevUsers => {
                        const updated = prevUsers.map(u => 
                            u.name === log.user ? { ...u, status: status as any } : u
                        );
                        // Persist immediately
                        localStorage.setItem('sentinel_users', JSON.stringify(updated));
                        return updated;
                    });
                    
                    // Add System Log for Action
                    setTimeout(() => {
                        addLogEntry(ActivityType.ADMIN, 'SOAR Action Executed', `Playbook '${rule.name}' triggered: Set ${log.user} to ${status}`);
                    }, 500);
                } else if (rule.action.type === 'ALERT_ADMIN') {
                     // Add Alert Log
                     setTimeout(() => {
                        addLogEntry(ActivityType.SYSTEM, 'High Priority Alert', `Playbook '${rule.name}' flagged activity by ${log.user}`);
                    }, 500);
                }
            }
        });
    };

    const addLogEntry = (type: ActivityType, desc: string, details: string, risk?: RiskLevel) => {
        const newLog: LogEntry = {
            id: Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toISOString(),
            user: currentUser ? currentUser.name : 'System',
            activityType: type,
            description: desc,
            details: details,
            riskLevel: risk || RiskLevel.LOW,
            ipAddress: '127.0.0.1',
            location: 'Internal Console'
        };
        setLogs(prev => [newLog, ...prev]);
        executePlaybooks(newLog); // Run Rule Engine
    };

    // User CRUD
    const addUser = (user: UserProfile) => {
        const updated = [...users, user];
        setUsers(updated);
        localStorage.setItem('sentinel_users', JSON.stringify(updated));
    };

    const updateUser = (updatedUser: UserProfile) => {
        const updated = users.map(u => u.id === updatedUser.id ? updatedUser : u);
        setUsers(updated);
        localStorage.setItem('sentinel_users', JSON.stringify(updated));
    };

    const deleteUser = (id: string) => {
        const updated = users.filter(u => u.id !== id);
        setUsers(updated);
        localStorage.setItem('sentinel_users', JSON.stringify(updated));
    };

    // Playbook CRUD
    const addRule = (rule: PlaybookRule) => {
        const updated = [...playbooks, rule];
        setPlaybooks(updated);
        localStorage.setItem('sentinel_playbooks', JSON.stringify(updated));
    };

    const toggleRule = (id: string) => {
        const updated = playbooks.map(r => r.id === id ? {...r, isActive: !r.isActive} : r);
        setPlaybooks(updated);
        localStorage.setItem('sentinel_playbooks', JSON.stringify(updated));
    };

    const deleteRule = (id: string) => {
        const updated = playbooks.filter(r => r.id !== id);
        setPlaybooks(updated);
        localStorage.setItem('sentinel_playbooks', JSON.stringify(updated));
    };

    // Simulated Traffic
    useEffect(() => {
        const interval = setInterval(() => {
            if (users.length === 0) return;

            const activeUsers = users.filter(u => u.status === 'ACTIVE');
            if (activeUsers.length === 0) return;

            const randomUser = activeUsers[Math.floor(Math.random() * activeUsers.length)];
            if (randomUser.id === currentUser?.id) return; 

            const types = [ActivityType.WEB, ActivityType.APP, ActivityType.SYSTEM, ActivityType.NETWORK];
            // 10% chance of high risk to trigger playbooks
            const isCritical = Math.random() > 0.90; 
            const risks = [RiskLevel.LOW, RiskLevel.LOW, RiskLevel.MEDIUM, isCritical ? RiskLevel.CRITICAL : RiskLevel.HIGH];
            
            const newLog: LogEntry = {
                id: Math.random().toString(36).substr(2, 9),
                timestamp: new Date().toISOString(),
                user: randomUser.name,
                activityType: types[Math.floor(Math.random() * types.length)],
                description: isCritical ? 'Unauthorized Root Access Attempt' : 'Standard user activity',
                details: `Automated system monitoring trace for ${randomUser.role}`,
                riskLevel: risks[Math.floor(Math.random() * risks.length)],
                ipAddress: `192.168.1.${Math.floor(Math.random() * 255)}`
            };

            setLogs(prevLogs => [newLog, ...prevLogs].slice(0, 100));
            executePlaybooks(newLog); // Run Rule Engine on simulated logs
        }, 4000); 

        return () => clearInterval(interval);
    }, [users, currentUser, playbooks]);

    const renderContent = () => {
        if (!currentUser) return null;

        const canManageUsers = currentUser.permissions.includes('MANAGE_USERS') || currentUser.role === 'Admin';
        const canEditSettings = currentUser.permissions.includes('EDIT_SETTINGS') || currentUser.role === 'Admin';
        const canReadLogs = currentUser.permissions.includes('READ_LOGS') || currentUser.role === 'Admin';

        switch (currentView) {
            case 'DASHBOARD':
                return <Dashboard logs={logs} />;
            case 'LIVE_MONITOR':
                return canReadLogs ? <ActivityLog logs={logs} /> : <AccessDenied />;
            case 'AI_ANALYST':
                return canReadLogs ? <AIAnalyst /> : <AccessDenied />;
            case 'AUTOMATION':
                return canEditSettings ? (
                    <PlaybookManager 
                        rules={playbooks}
                        onAddRule={addRule}
                        onDeleteRule={deleteRule}
                        onToggleRule={toggleRule}
                    />
                ) : <AccessDenied />;
            case 'USERS':
                return canManageUsers ? (
                    <UserManagement 
                        users={users} 
                        onAddUser={addUser} 
                        onUpdateUser={updateUser} 
                        onDeleteUser={deleteUser}
                        onActionLog={(type, desc, details) => addLogEntry(type, desc, details)}
                    />
                ) : <AccessDenied />;
            case 'SETTINGS':
                return canEditSettings ? <Settings /> : <AccessDenied />;
            default:
                return <Dashboard logs={logs} />;
        }
    };

    const AccessDenied = () => (
        <div className="flex flex-col items-center justify-center h-full text-slate-500 animate-fadeIn">
            <div className="w-20 h-20 bg-slate-900 rounded-full flex items-center justify-center mb-4 border border-slate-700">
                <Lock size={40} className="text-red-500" />
            </div>
            <h2 className="text-2xl font-bold text-white">Access Denied</h2>
            <p className="mt-2">Your clearance level does not permit access to this sector.</p>
        </div>
    );

    if (!currentUser) {
        return <Login onLogin={handleLogin} error={loginError} />;
    }

    return (
        <div className="flex min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
            {/* Background Effects */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cyan-900/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-900/10 rounded-full blur-[120px]" />
                <div className="absolute top-0 left-0 w-full h-full opacity-[0.03]" style={{
                    backgroundImage: `linear-gradient(#1e293b 1px, transparent 1px), linear-gradient(to right, #1e293b 1px, transparent 1px)`,
                    backgroundSize: '40px 40px'
                }} />
            </div>

            <Sidebar 
                currentView={currentView} 
                onChangeView={setCurrentView} 
                currentUser={currentUser}
                onLogout={handleLogout}
            />

            <main className="flex-1 ml-64 p-8 relative z-10 h-screen overflow-y-auto scroll-smooth">
                {renderContent()}
            </main>
        </div>
    );
};

export default App;