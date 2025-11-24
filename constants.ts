import { ActivityType, LogEntry, RiskLevel } from './types';
import { ShieldAlert, Globe, Smartphone, Server } from 'lucide-react';

export const MOCK_LOGS: LogEntry[] = [
    {
        id: '1',
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        user: 'alice.w',
        activityType: ActivityType.WEB,
        description: 'Access to restricted domain',
        details: 'Attempted to access gambling-site-x.com',
        riskLevel: RiskLevel.HIGH,
        ipAddress: '192.168.1.105',
        location: 'Internal Network'
    },
    {
        id: '2',
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
        user: 'system',
        activityType: ActivityType.NETWORK,
        description: 'Port scan detected',
        details: 'Rapid connection attempts on ports 20-1024',
        riskLevel: RiskLevel.CRITICAL,
        ipAddress: '45.22.19.112',
        location: 'Unknown (External)'
    },
    {
        id: '3',
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        user: 'bob.m',
        activityType: ActivityType.APP,
        description: 'Productivity Application',
        details: 'Launched VS Code',
        riskLevel: RiskLevel.LOW,
        ipAddress: '192.168.1.106',
        location: 'Office A'
    },
    {
        id: '4',
        timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
        user: 'charlie.d',
        activityType: ActivityType.WEB,
        description: 'Large file upload',
        details: 'Upload 2.5GB to personal-cloud-storage.net',
        riskLevel: RiskLevel.MEDIUM,
        ipAddress: '192.168.1.107',
        location: 'Remote VPN'
    },
    {
        id: '5',
        timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
        user: 'alice.w',
        activityType: ActivityType.SYSTEM,
        description: 'USB Device Attached',
        details: 'Mass Storage Device (VendorID: 0x1234)',
        riskLevel: RiskLevel.MEDIUM,
        ipAddress: '192.168.1.105',
        location: 'Office A'
    }
];

export const MOCK_STATS = [
    { title: 'Threats Blocked', value: 124, trend: 12, icon: 'ShieldAlert', color: 'text-red-400' },
    { title: 'Active Sessions', value: 42, trend: -5, icon: 'Globe', color: 'text-blue-400' },
    { title: 'Data Violations', value: 3, trend: 0, icon: 'Server', color: 'text-yellow-400' },
];
