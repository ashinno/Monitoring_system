import React from 'react';

export enum RiskLevel {
    LOW = 'LOW',
    MEDIUM = 'MEDIUM',
    HIGH = 'HIGH',
    CRITICAL = 'CRITICAL'
}

export enum ActivityType {
    WEB = 'WEB',
    APP = 'APP',
    SYSTEM = 'SYSTEM',
    NETWORK = 'NETWORK',
    ADMIN = 'ADMIN'
}

export interface LogEntry {
    id: string;
    timestamp: string;
    user: string;
    activityType: ActivityType;
    description: string;
    details: string;
    riskLevel: RiskLevel;
    ipAddress?: string;
    location?: string;
}

export interface UserProfile {
    id: string;
    name: string;
    role: string;
    clearanceLevel: 'L1' | 'L2' | 'L3' | 'ADMIN';
    status: 'ACTIVE' | 'INACTIVE' | 'LOCKED' | 'SUSPENDED' | 'QUARANTINED';
    avatarSeed?: string;
    permissions: string[]; // e.g., 'READ_LOGS', 'EDIT_SETTINGS'
    password?: string; // Storing strictly for demo purposes
}

export interface AnalysisResult {
    summary: string;
    threatScore: number; // 0-100
    recommendations: string[];
    flaggedLogs: string[];
}

export type ViewState = 'DASHBOARD' | 'LIVE_MONITOR' | 'AI_ANALYST' | 'SETTINGS' | 'USERS' | 'AUTOMATION';

export interface StatCardProps {
    title: string;
    value: string | number;
    trend?: number; // percentage
    icon: React.ReactNode;
    color?: string;
}

// Automation / SOAR Types
export interface PlaybookRule {
    id: string;
    name: string;
    isActive: boolean;
    trigger: {
        field: 'riskLevel' | 'activityType' | 'description';
        operator: 'equals' | 'contains';
        value: string;
    };
    action: {
        type: 'LOCK_USER' | 'ALERT_ADMIN' | 'QUARANTINE_USER';
        target?: string;
    };
}