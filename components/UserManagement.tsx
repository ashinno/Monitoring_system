import React, { useState } from 'react';
import { UserPlus, Trash2, Shield, User, Key, MoreVertical, Power, RefreshCw, Lock, Check, X, Search, Filter, Briefcase, AlertTriangle } from 'lucide-react';
import { UserProfile, ActivityType } from '../types';

interface UserManagementProps {
    users: UserProfile[];
    onAddUser: (user: UserProfile) => void;
    onUpdateUser: (user: UserProfile) => void;
    onDeleteUser: (id: string) => void;
    onActionLog: (type: ActivityType, desc: string, details: string) => void;
}

const UserManagement: React.FC<UserManagementProps> = ({ users, onAddUser, onUpdateUser, onDeleteUser, onActionLog }) => {
    const [isAdding, setIsAdding] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [filterClearance, setFilterClearance] = useState('ALL');
    const [filterRole, setFilterRole] = useState('ALL');

    const [newUser, setNewUser] = useState({ name: '', role: '', clearance: 'L1', password: '' });
    const [newPermissions, setNewPermissions] = useState<string[]>([]);
    const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

    // Confirmation Modal State
    const [pendingStatusChange, setPendingStatusChange] = useState<{user: UserProfile, status: UserProfile['status']} | null>(null);

    // Password Policy State
    const [pwdValidations, setPwdValidations] = useState({
        length: false,
        upper: false,
        number: false,
        special: false
    });

    // Derive unique roles for filter
    const uniqueRoles = Array.from(new Set(users.map(u => u.role)));

    const checkPassword = (pwd: string) => {
        setPwdValidations({
            length: pwd.length >= 8,
            upper: /[A-Z]/.test(pwd),
            number: /[0-9]/.test(pwd),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(pwd)
        });
        setNewUser(prev => ({ ...prev, password: pwd }));
    };

    const isPasswordValid = Object.values(pwdValidations).every(v => v);

    const availablePermissions = [
        { id: 'READ_LOGS', label: 'Read Logs' },
        { id: 'EDIT_SETTINGS', label: 'Modify Policy' },
        { id: 'MANAGE_USERS', label: 'Manage Users' },
        { id: 'EXPORT_DATA', label: 'Export Data' }
    ];

    const rolesPresets: Record<string, string[]> = {
        'Administrator': ['READ_LOGS', 'EDIT_SETTINGS', 'MANAGE_USERS', 'EXPORT_DATA'],
        'Security Analyst': ['READ_LOGS', 'EXPORT_DATA'],
        'Auditor': ['READ_LOGS'],
        'Standard User': []
    };

    const handleRoleChange = (role: string) => {
        setNewUser({ ...newUser, role });
        // Auto-select permissions based on role preset
        if (rolesPresets[role]) {
            setNewPermissions(rolesPresets[role]);
        }
    };

    const togglePermission = (perm: string) => {
        setNewPermissions(prev => 
            prev.includes(perm) ? prev.filter(p => p !== perm) : [...prev, perm]
        );
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!newUser.name || !newUser.role || !isPasswordValid) return;

        const user: UserProfile = {
            id: Math.random().toString(36).substr(2, 9),
            name: newUser.name,
            role: newUser.role,
            clearanceLevel: newUser.clearance as any,
            status: 'ACTIVE',
            avatarSeed: Math.random().toString(),
            permissions: newPermissions,
            password: newUser.password
        };

        onAddUser(user);
        onActionLog(ActivityType.ADMIN, 'User Created', `Created profile for ${user.name} as ${user.role}`);
        
        // Reset
        setNewUser({ name: '', role: '', clearance: 'L1', password: '' });
        setNewPermissions([]);
        setPwdValidations({ length: false, upper: false, number: false, special: false });
        setIsAdding(false);
    };

    const handleStatusChangeClick = (user: UserProfile, newStatus: UserProfile['status']) => {
        setPendingStatusChange({ user, status: newStatus });
        setActiveMenuId(null);
    };

    const confirmStatusChange = () => {
        if (pendingStatusChange) {
            const { user, status } = pendingStatusChange;
            const updatedUser = { ...user, status: status };
            onUpdateUser(updatedUser);
            onActionLog(ActivityType.ADMIN, 'User Status Changed', `Changed status of ${user.name} to ${status}`);
            setPendingStatusChange(null);
        }
    };

    const handleDelete = (user: UserProfile) => {
        if(window.confirm(`Are you sure you want to remove ${user.name}? This cannot be undone.`)) {
            onDeleteUser(user.id);
            onActionLog(ActivityType.ADMIN, 'User Deleted', `Removed profile for ${user.name}`);
        }
    };

    const filteredUsers = users.filter(user => {
        const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                              user.role.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'ALL' || user.status === filterStatus;
        const matchesClearance = filterClearance === 'ALL' || user.clearanceLevel === filterClearance;
        const matchesRole = filterRole === 'ALL' || user.role === filterRole;

        return matchesSearch && matchesStatus && matchesClearance && matchesRole;
    });

    return (
        <div className="space-y-6 animate-fadeIn pb-10" onClick={() => setActiveMenuId(null)}>
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">User Access Control</h2>
                    <p className="text-slate-400 mt-1">Manage personnel clearance, roles, and fine-grained permissions.</p>
                </div>
                <button 
                    onClick={(e) => { e.stopPropagation(); setIsAdding(!isAdding); }}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-all shadow-neon"
                >
                    <UserPlus size={18} />
                    Add User
                </button>
            </div>

            {/* Filter Toolbar */}
            <div className="glass-panel p-4 rounded-xl flex flex-wrap gap-4 items-center">
                <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input 
                        type="text" 
                        placeholder="Search users..." 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-slate-900/80 border border-slate-700 rounded-lg py-2 pl-10 pr-4 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                </div>
                
                <div className="flex items-center gap-2 flex-wrap">
                    {/* Status Filter */}
                    <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2">
                         <Filter className="text-slate-500" size={16} />
                        <select 
                            className="bg-transparent text-sm text-slate-300 focus:outline-none"
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                        >
                            <option value="ALL">All Status</option>
                            <option value="ACTIVE">Active</option>
                            <option value="INACTIVE">Inactive</option>
                            <option value="LOCKED">Locked</option>
                            <option value="SUSPENDED">Suspended</option>
                            <option value="QUARANTINED">Quarantined</option>
                        </select>
                    </div>

                    {/* Role Filter */}
                    <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2">
                         <Briefcase className="text-slate-500" size={16} />
                        <select 
                            className="bg-transparent text-sm text-slate-300 focus:outline-none max-w-[120px]"
                            value={filterRole}
                            onChange={(e) => setFilterRole(e.target.value)}
                        >
                            <option value="ALL">All Roles</option>
                            {uniqueRoles.map(role => (
                                <option key={role} value={role}>{role}</option>
                            ))}
                        </select>
                    </div>

                    {/* Clearance Filter */}
                    <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2">
                         <Shield className="text-slate-500" size={16} />
                        <select 
                            className="bg-transparent text-sm text-slate-300 focus:outline-none"
                            value={filterClearance}
                            onChange={(e) => setFilterClearance(e.target.value)}
                        >
                            <option value="ALL">All Levels</option>
                            <option value="L1">Level 1</option>
                            <option value="L2">Level 2</option>
                            <option value="L3">Level 3</option>
                            <option value="ADMIN">Admin</option>
                        </select>
                    </div>
                </div>
            </div>

            {isAdding && (
                <div className="glass-panel p-6 rounded-xl border border-cyan-500/30 animate-slideDown" onClick={e => e.stopPropagation()}>
                    <h3 className="text-lg font-semibold text-white mb-4">New Profile Registration</h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">Full Name</label>
                                    <input 
                                        type="text" 
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:border-cyan-500 outline-none"
                                        value={newUser.name}
                                        onChange={e => setNewUser({...newUser, name: e.target.value})}
                                        placeholder="ex. John Doe"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">Role / Designation</label>
                                    <select 
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:border-cyan-500 outline-none"
                                        value={newUser.role}
                                        onChange={e => handleRoleChange(e.target.value)}
                                    >
                                        <option value="" disabled>Select Role</option>
                                        {Object.keys(rolesPresets).map(role => (
                                            <option key={role} value={role}>{role}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">Clearance Level</label>
                                    <select 
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:border-cyan-500 outline-none"
                                        value={newUser.clearance}
                                        onChange={e => setNewUser({...newUser, clearance: e.target.value})}
                                    >
                                        <option value="L1">Level 1 (Basic)</option>
                                        <option value="L2">Level 2 (Elevated)</option>
                                        <option value="L3">Level 3 (Confidential)</option>
                                        <option value="ADMIN">Administrator</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">Set Password</label>
                                    <div className="relative">
                                        <input 
                                            type="text" // Visible for demo/admin purposes
                                            className={`w-full bg-slate-900 border ${isPasswordValid && newUser.password ? 'border-green-500/50' : 'border-slate-700'} rounded-lg p-2 text-white focus:border-cyan-500 outline-none`}
                                            value={newUser.password}
                                            onChange={e => checkPassword(e.target.value)}
                                            placeholder="Enter strong password"
                                        />
                                        {isPasswordValid && newUser.password && <Check className="absolute right-2 top-2 text-green-500" size={16} />}
                                    </div>
                                    
                                    {/* Password Policy Visualizer */}
                                    <div className="mt-2 grid grid-cols-2 gap-2">
                                        <div className={`text-[10px] flex items-center gap-1 ${pwdValidations.length ? 'text-green-400' : 'text-slate-500'}`}>
                                            {pwdValidations.length ? <Check size={10} /> : <div className="w-2.5 h-2.5 rounded-full border border-slate-600" />} 8+ Characters
                                        </div>
                                        <div className={`text-[10px] flex items-center gap-1 ${pwdValidations.upper ? 'text-green-400' : 'text-slate-500'}`}>
                                            {pwdValidations.upper ? <Check size={10} /> : <div className="w-2.5 h-2.5 rounded-full border border-slate-600" />} Uppercase Letter
                                        </div>
                                        <div className={`text-[10px] flex items-center gap-1 ${pwdValidations.number ? 'text-green-400' : 'text-slate-500'}`}>
                                            {pwdValidations.number ? <Check size={10} /> : <div className="w-2.5 h-2.5 rounded-full border border-slate-600" />} Number
                                        </div>
                                        <div className={`text-[10px] flex items-center gap-1 ${pwdValidations.special ? 'text-green-400' : 'text-slate-500'}`}>
                                            {pwdValidations.special ? <Check size={10} /> : <div className="w-2.5 h-2.5 rounded-full border border-slate-600" />} Special Char
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs text-slate-400 mb-2">Assign Permissions</label>
                                    <div className="flex flex-wrap gap-2">
                                        {availablePermissions.map(perm => (
                                            <label key={perm.id} className={`flex items-center gap-2 cursor-pointer p-2 rounded border transition-colors ${newPermissions.includes(perm.id) ? 'bg-cyan-500/20 border-cyan-500/50' : 'bg-slate-900 border-slate-800'}`}>
                                                <input 
                                                    type="checkbox" 
                                                    checked={newPermissions.includes(perm.id)}
                                                    onChange={() => togglePermission(perm.id)}
                                                    className="hidden"
                                                />
                                                <span className={`text-xs ${newPermissions.includes(perm.id) ? 'text-cyan-300' : 'text-slate-400'}`}>{perm.label}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
                             <button type="button" onClick={() => setIsAdding(false)} className="px-4 py-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white text-sm">Cancel</button>
                             <button 
                                type="submit" 
                                disabled={!isPasswordValid || !newUser.name || !newUser.role}
                                className="px-6 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500 font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Create Profile
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredUsers.map(user => (
                    <div key={user.id} className={`glass-panel p-5 rounded-xl group relative overflow-visible transition-all duration-300 hover:border-slate-600 ${
                        user.status === 'LOCKED' || user.status === 'QUARANTINED' ? 'border-red-500/30 bg-red-900/10' : 
                        user.status === 'INACTIVE' || user.status === 'SUSPENDED' ? 'opacity-60 grayscale-[0.5]' : ''
                    }`}>
                        
                        <div className="absolute top-4 right-4 z-10">
                             <button 
                                onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === user.id ? null : user.id); }}
                                className="text-slate-500 hover:text-cyan-400 transition-colors p-1"
                             >
                                 <MoreVertical size={18} />
                             </button>

                             {activeMenuId === user.id && (
                                 <div className="absolute right-0 top-8 w-48 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-20 py-1 flex flex-col">
                                     <div className="px-3 py-2 text-[10px] text-slate-500 font-mono uppercase border-b border-slate-800">
                                        Set Status
                                     </div>
                                     {['ACTIVE', 'INACTIVE', 'SUSPENDED', 'LOCKED', 'QUARANTINED'].map((status) => (
                                         <button 
                                            key={status}
                                            onClick={(e) => { e.stopPropagation(); handleStatusChangeClick(user, status as any); }}
                                            className={`px-4 py-2 text-sm text-left hover:bg-slate-800 flex items-center gap-2 ${user.status === status ? 'text-cyan-400' : 'text-slate-400'}`}
                                        >
                                            <div className={`w-2 h-2 rounded-full ${user.status === status ? 'bg-cyan-400' : 'bg-slate-600'}`} />
                                            {status}
                                        </button>
                                     ))}
                                     <div className="h-px bg-slate-800 my-1" />
                                     <button 
                                        onClick={(e) => { e.stopPropagation(); handleDelete(user); }}
                                        className="px-4 py-2 text-sm text-left text-red-400 hover:bg-slate-800 flex items-center gap-2"
                                     >
                                         <Trash2 size={14} />
                                         Remove Profile
                                     </button>
                                 </div>
                             )}
                        </div>
                        
                        <div className="flex items-start gap-4">
                            {/* Generated SVG Avatar */}
                            <div className="w-12 h-12 rounded-lg bg-slate-900 border border-slate-700 overflow-hidden flex-shrink-0">
                                <svg viewBox="0 0 100 100" className="w-full h-full">
                                    <rect width="100" height="100" fill="#0f172a" />
                                    <circle cx="50" cy="40" r="20" fill={`hsl(${parseInt(user.avatarSeed || '0') * 360}, 70%, 60%)`} opacity="0.8" />
                                    <rect x="20" y="70" width="60" height="40" rx="10" fill={`hsl(${parseInt(user.avatarSeed || '0') * 360}, 60%, 40%)`} />
                                    <path d="M0 0 L100 100" stroke="rgba(255,255,255,0.1)" strokeWidth="2" />
                                </svg>
                            </div>

                            <div>
                                <h3 className="text-white font-bold">{user.name}</h3>
                                <p className="text-cyan-500 text-xs font-mono mb-1">{user.role}</p>
                                <div className="flex gap-2 mt-2">
                                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-slate-400 font-mono flex items-center gap-1">
                                        <Key size={10} /> {user.id}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                                        user.clearanceLevel === 'ADMIN' ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' :
                                        user.clearanceLevel === 'L3' ? 'bg-red-500/10 border-red-500/30 text-red-400' :
                                        'bg-blue-500/10 border-blue-500/30 text-blue-400'
                                    }`}>
                                        {user.clearanceLevel}
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        {/* Permissions Chips */}
                        <div className="mt-3 flex flex-wrap gap-1 min-h-[24px]">
                            {user.permissions && user.permissions.map(perm => (
                                <span key={perm} className="text-[10px] px-2 py-0.5 bg-slate-800/50 text-slate-500 rounded border border-slate-800">
                                    {perm.split('_')[1] || perm}
                                </span>
                            ))}
                        </div>

                        <div className="mt-4 pt-4 border-t border-slate-800 flex justify-between items-center">
                            <span className="text-xs text-slate-500">Status</span>
                            <span className={`flex items-center gap-1.5 text-xs font-mono 
                                ${user.status === 'ACTIVE' ? 'text-green-400' : 
                                  user.status === 'LOCKED' ? 'text-red-400' : 
                                  user.status === 'QUARANTINED' ? 'text-yellow-400' : 'text-slate-500'}`}>
                                <span className={`w-1.5 h-1.5 rounded-full 
                                    ${user.status === 'ACTIVE' ? 'bg-green-500 animate-pulse' : 
                                      user.status === 'LOCKED' ? 'bg-red-500' : 
                                      user.status === 'QUARANTINED' ? 'bg-yellow-500 animate-bounce' : 'bg-slate-500'}`} 
                                />
                                {user.status}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
            {filteredUsers.length === 0 && (
                <div className="text-center py-10 text-slate-500">
                    No users found matching your criteria.
                </div>
            )}

            {/* Status Change Confirmation Modal */}
            {pendingStatusChange && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setPendingStatusChange(null)} />
                    
                    <div className="relative bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full shadow-2xl animate-fadeIn">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="w-12 h-12 rounded-full bg-yellow-500/10 flex items-center justify-center border border-yellow-500/30">
                                <AlertTriangle className="text-yellow-500" size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Confirm Status Change</h3>
                                <p className="text-sm text-slate-400">Security Clearance Modification</p>
                            </div>
                        </div>

                        <p className="text-slate-300 text-sm leading-relaxed mb-6">
                            Are you sure you want to change the status of <strong className="text-white">{pendingStatusChange.user.name}</strong> to <strong className={`font-mono ${
                                pendingStatusChange.status === 'ACTIVE' ? 'text-green-400' : 'text-red-400'
                            }`}>{pendingStatusChange.status}</strong>?
                            <br/><br/>
                            {pendingStatusChange.status === 'LOCKED' || pendingStatusChange.status === 'QUARANTINED' 
                                ? "This will immediately restrict the user's access to system resources." 
                                : "This will restore standard access privileges."}
                        </p>

                        <div className="flex justify-end gap-3">
                            <button 
                                onClick={() => setPendingStatusChange(null)}
                                className="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors text-sm font-medium"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={confirmStatusChange}
                                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-bold shadow-lg shadow-cyan-900/20"
                            >
                                Confirm Change
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserManagement;