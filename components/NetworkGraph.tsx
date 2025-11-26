import React, { useEffect, useState, useRef, useMemo } from 'react';
import { LogEntry, RiskLevel } from '../types';

interface NetworkGraphProps {
    logs: LogEntry[];
}

interface Node {
    id: string;
    type: 'USER' | 'IP';
    label: string;
    x: number;
    y: number;
    vx: number;
    vy: number;
}

interface Link {
    source: string;
    target: string;
    riskLevel: RiskLevel;
}

const NetworkGraph: React.FC<NetworkGraphProps> = ({ logs }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const [nodes, setNodes] = useState<Node[]>([]);
    const [links, setLinks] = useState<Link[]>([]);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);

    // Process data
    useEffect(() => {
        const userSet = new Set<string>();
        const ipSet = new Set<string>();
        const linkMap = new Map<string, RiskLevel>();

        logs.forEach(log => {
            if (!log.user || !log.ipAddress) return;
            
            userSet.add(log.user);
            ipSet.add(log.ipAddress);

            const linkId = `${log.user}-${log.ipAddress}`;
            const currentRisk = linkMap.get(linkId);
            
            // Upgrade risk if we find a higher one
            if (!currentRisk || getRiskScore(log.riskLevel) > getRiskScore(currentRisk)) {
                linkMap.set(linkId, log.riskLevel);
            }
        });

        const newNodes: Node[] = [
            ...Array.from(userSet).map(u => ({
                id: `user-${u}`,
                type: 'USER' as const,
                label: u,
                x: Math.random() * 800,
                y: Math.random() * 600,
                vx: 0,
                vy: 0
            })),
            ...Array.from(ipSet).map(ip => ({
                id: `ip-${ip}`,
                type: 'IP' as const,
                label: ip,
                x: Math.random() * 800,
                y: Math.random() * 600,
                vx: 0,
                vy: 0
            }))
        ];

        const newLinks: Link[] = Array.from(linkMap.entries()).map(([key, risk]) => {
            const [user, ip] = key.split('-'); // simple split might fail if user has dash, but assuming simple usernames
            // Better split: find the known user and ip? 
            // Actually, let's store structured keys in map or just iterate logs again?
            // Re-iterating logs is safer but might duplicate.
            // Let's use a composite key object map or just be careful.
            // Since we built userSet and ipSet, we can reconstruct.
            // But map keys are strings. 
            // Let's assume usernames don't contain " - " or something.
            // Wait, I can just store the link objects in a list and deduplicate.
            return {
                source: `user-${user}`, // Using the prefix to match node IDs
                target: `ip-${ip}`,
                riskLevel: risk
            };
        });
        // Fix split issue: user might be "John-Doe". 
        // Let's re-do link construction to be safe.
        const safeLinks: Link[] = [];
        const processedLinks = new Set<string>();
        
        logs.forEach(log => {
            if (!log.user || !log.ipAddress) return;
            const sourceId = `user-${log.user}`;
            const targetId = `ip-${log.ipAddress}`;
            const linkKey = `${sourceId}|${targetId}`;
            
            if (!processedLinks.has(linkKey)) {
                processedLinks.add(linkKey);
                safeLinks.push({
                    source: sourceId,
                    target: targetId,
                    riskLevel: log.riskLevel
                });
            } else {
                // Update risk if needed (find existing and update)
                const existing = safeLinks.find(l => l.source === sourceId && l.target === targetId);
                if (existing && getRiskScore(log.riskLevel) > getRiskScore(existing.riskLevel)) {
                    existing.riskLevel = log.riskLevel;
                }
            }
        });

        setNodes(newNodes);
        setLinks(safeLinks);
    }, [logs]);

    // Force Simulation
    useEffect(() => {
        if (nodes.length === 0) return;

        let animationFrameId: number;
        const width = 800;
        const height = 500;
        const k = 0.1; // Spring constant
        const repulsion = 5000;
        const damping = 0.85;
        const centerForce = 0.05;

        const tick = () => {
            setNodes(prevNodes => {
                const nextNodes = prevNodes.map(n => ({ ...n }));
                
                // 1. Repulsion
                for (let i = 0; i < nextNodes.length; i++) {
                    for (let j = i + 1; j < nextNodes.length; j++) {
                        const dx = nextNodes[i].x - nextNodes[j].x;
                        const dy = nextNodes[i].y - nextNodes[j].y;
                        const distSq = dx * dx + dy * dy || 1;
                        const force = repulsion / distSq;
                        const fx = (dx / Math.sqrt(distSq)) * force;
                        const fy = (dy / Math.sqrt(distSq)) * force;

                        nextNodes[i].vx += fx;
                        nextNodes[i].vy += fy;
                        nextNodes[j].vx -= fx;
                        nextNodes[j].vy -= fy;
                    }
                }

                // 2. Attraction (Springs)
                links.forEach(link => {
                    const source = nextNodes.find(n => n.id === link.source);
                    const target = nextNodes.find(n => n.id === link.target);
                    if (source && target) {
                        const dx = target.x - source.x;
                        const dy = target.y - source.y;
                        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                        const force = (dist - 100) * k; // 100 is ideal length
                        const fx = (dx / dist) * force;
                        const fy = (dy / dist) * force;

                        source.vx += fx;
                        source.vy += fy;
                        target.vx -= fx;
                        target.vy -= fy;
                    }
                });

                // 3. Center Gravity & Movement
                nextNodes.forEach(node => {
                    const dx = width / 2 - node.x;
                    const dy = height / 2 - node.y;
                    
                    node.vx += dx * centerForce;
                    node.vy += dy * centerForce;

                    node.x += node.vx;
                    node.y += node.vy;
                    
                    node.vx *= damping;
                    node.vy *= damping;
                    
                    // Boundaries
                    node.x = Math.max(20, Math.min(width - 20, node.x));
                    node.y = Math.max(20, Math.min(height - 20, node.y));
                });

                return nextNodes;
            });

            animationFrameId = requestAnimationFrame(tick);
        };

        tick();

        return () => cancelAnimationFrame(animationFrameId);
    }, [links.length]); // Re-run if graph structure changes (initial load mainly)
    // Note: We don't depend on 'nodes' or it would loop infinitely. 
    // We use functional state update to access latest nodes.

    const getRiskScore = (risk: RiskLevel) => {
        switch (risk) {
            case RiskLevel.CRITICAL: return 4;
            case RiskLevel.HIGH: return 3;
            case RiskLevel.MEDIUM: return 2;
            case RiskLevel.LOW: return 1;
            default: return 0;
        }
    };

    const getLinkColor = (risk: RiskLevel) => {
        if (risk === RiskLevel.CRITICAL) return '#ef4444'; // red-500
        if (risk === RiskLevel.HIGH) return '#f97316'; // orange-500
        return '#475569'; // slate-600
    };

    const isConnected = (nodeId: string, link: Link) => {
        return link.source === nodeId || link.target === nodeId;
    };

    return (
        <div className="glass-panel p-6 rounded-xl border-t-4 border-t-purple-500 w-full animate-fadeIn">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        Lateral Movement Map
                    </h3>
                    <p className="text-slate-400 text-sm mt-1">
                        Visualizing user-to-IP relationships and potential blast radius.
                    </p>
                </div>
                <div className="flex gap-4 text-xs">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-cyan-500"></div>
                        <span className="text-slate-300">User</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-purple-500" style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}></div>
                        <span className="text-slate-300">IP Address</span>
                    </div>
                </div>
            </div>

            <div className="w-full h-[500px] bg-slate-900/50 rounded-lg overflow-hidden relative">
                <svg ref={svgRef} viewBox="0 0 800 500" className="w-full h-full">
                    <defs>
                        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="#475569" />
                        </marker>
                    </defs>

                    {/* Links */}
                    {links.map((link, i) => {
                        const sourceNode = nodes.find(n => n.id === link.source);
                        const targetNode = nodes.find(n => n.id === link.target);
                        if (!sourceNode || !targetNode) return null;

                        const isHighRisk = link.riskLevel === RiskLevel.CRITICAL;
                        const isActive = hoveredNode ? isConnected(hoveredNode, link) : true;
                        
                        return (
                            <line 
                                key={i}
                                x1={sourceNode.x} y1={sourceNode.y}
                                x2={targetNode.x} y2={targetNode.y}
                                stroke={getLinkColor(link.riskLevel)}
                                strokeWidth={isHighRisk ? 3 : 1}
                                strokeOpacity={isActive ? 1 : 0.1}
                                className={isHighRisk ? 'animate-pulse' : ''}
                            />
                        );
                    })}

                    {/* Nodes */}
                    {nodes.map(node => {
                        const isHovered = hoveredNode === node.id;
                        const isDimmed = hoveredNode && hoveredNode !== node.id && !links.some(l => isConnected(hoveredNode, l) && isConnected(node.id, l));

                        return (
                            <g 
                                key={node.id} 
                                transform={`translate(${node.x},${node.y})`}
                                onMouseEnter={() => setHoveredNode(node.id)}
                                onMouseLeave={() => setHoveredNode(null)}
                                className={`transition-opacity duration-300 ${isDimmed ? 'opacity-20' : 'opacity-100'} cursor-pointer`}
                            >
                                {node.type === 'USER' ? (
                                    <circle 
                                        r={20} 
                                        fill="#06b6d4" // cyan-500
                                        stroke="#ecfeff" 
                                        strokeWidth={isHovered ? 2 : 0}
                                    />
                                ) : (
                                    <polygon 
                                        points="-18,-10 0,-20 18,-10 18,10 0,20 -18,10"
                                        fill="#a855f7" // purple-500
                                        stroke="#f3e8ff"
                                        strokeWidth={isHovered ? 2 : 0}
                                    />
                                )}
                                
                                <text 
                                    y={35} 
                                    textAnchor="middle" 
                                    fill="white" 
                                    fontSize="12"
                                    className="pointer-events-none select-none font-mono"
                                >
                                    {node.label}
                                </text>
                            </g>
                        );
                    })}
                </svg>
            </div>
        </div>
    );
};

export default NetworkGraph;
