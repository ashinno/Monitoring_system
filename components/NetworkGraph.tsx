import React, { useEffect, useMemo, useRef, useState } from 'react';
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

interface ViewTransform {
    scale: number;
    x: number;
    y: number;
}

const WIDTH = 800;
const HEIGHT = 500;

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
    if (risk === RiskLevel.CRITICAL) return '#ef4444';
    if (risk === RiskLevel.HIGH) return '#f97316';
    if (risk === RiskLevel.MEDIUM) return '#eab308';
    return '#475569';
};

const linkId = (link: Link) => `${link.source}|${link.target}`;

const riskOrder: RiskLevel[] = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW];

const NetworkGraph: React.FC<NetworkGraphProps> = ({ logs }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const [nodes, setNodes] = useState<Node[]>([]);
    const [links, setLinks] = useState<Link[]>([]);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<string | null>(null);
    const [selectedLink, setSelectedLink] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [draggingNode, setDraggingNode] = useState<string | null>(null);
    const [isPanning, setIsPanning] = useState(false);
    const [viewTransform, setViewTransform] = useState<ViewTransform>({ scale: 1, x: 0, y: 0 });
    const [riskFilters, setRiskFilters] = useState<Record<RiskLevel, boolean>>({
        [RiskLevel.CRITICAL]: true,
        [RiskLevel.HIGH]: true,
        [RiskLevel.MEDIUM]: true,
        [RiskLevel.LOW]: true
    });
    const draggingNodeRef = useRef<string | null>(null);
    const panStartRef = useRef({ x: 0, y: 0, startX: 0, startY: 0 });

    useEffect(() => {
        draggingNodeRef.current = draggingNode;
    }, [draggingNode]);

    useEffect(() => {
        const userSet = new Set<string>();
        const ipSet = new Set<string>();
        const safeLinks: Link[] = [];
        const processedLinks = new Set<string>();

        logs.forEach(log => {
            if (!log.user || !log.ipAddress) return;
            userSet.add(log.user);
            ipSet.add(log.ipAddress);

            const sourceId = `user-${log.user}`;
            const targetId = `ip-${log.ipAddress}`;
            const key = `${sourceId}|${targetId}`;

            if (!processedLinks.has(key)) {
                processedLinks.add(key);
                safeLinks.push({
                    source: sourceId,
                    target: targetId,
                    riskLevel: log.riskLevel
                });
            } else {
                const existing = safeLinks.find(l => l.source === sourceId && l.target === targetId);
                if (existing && getRiskScore(log.riskLevel) > getRiskScore(existing.riskLevel)) {
                    existing.riskLevel = log.riskLevel;
                }
            }
        });

        const newNodes: Node[] = [
            ...Array.from(userSet).map(user => ({
                id: `user-${user}`,
                type: 'USER' as const,
                label: user,
                x: Math.random() * WIDTH,
                y: Math.random() * HEIGHT,
                vx: 0,
                vy: 0
            })),
            ...Array.from(ipSet).map(ip => ({
                id: `ip-${ip}`,
                type: 'IP' as const,
                label: ip,
                x: Math.random() * WIDTH,
                y: Math.random() * HEIGHT,
                vx: 0,
                vy: 0
            }))
        ];

        setNodes(newNodes);
        setLinks(safeLinks);
    }, [logs]);

    useEffect(() => {
        if (nodes.length === 0) return;

        let animationFrameId: number;
        const k = 0.1;
        const repulsion = 5000;
        const damping = 0.85;
        const centerForce = 0.05;

        const tick = () => {
            setNodes(prevNodes => {
                const nextNodes = prevNodes.map(n => ({ ...n }));

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

                links.forEach(link => {
                    const source = nextNodes.find(n => n.id === link.source);
                    const target = nextNodes.find(n => n.id === link.target);
                    if (!source || !target) return;
                    const dx = target.x - source.x;
                    const dy = target.y - source.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    const force = (dist - 100) * k;
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;

                    source.vx += fx;
                    source.vy += fy;
                    target.vx -= fx;
                    target.vy -= fy;
                });

                nextNodes.forEach(node => {
                    if (draggingNodeRef.current === node.id) {
                        node.vx = 0;
                        node.vy = 0;
                        return;
                    }

                    const dx = WIDTH / 2 - node.x;
                    const dy = HEIGHT / 2 - node.y;

                    node.vx += dx * centerForce;
                    node.vy += dy * centerForce;
                    node.x += node.vx;
                    node.y += node.vy;
                    node.vx *= damping;
                    node.vy *= damping;
                    node.x = Math.max(20, Math.min(WIDTH - 20, node.x));
                    node.y = Math.max(20, Math.min(HEIGHT - 20, node.y));
                });

                return nextNodes;
            });

            animationFrameId = requestAnimationFrame(tick);
        };

        tick();
        return () => cancelAnimationFrame(animationFrameId);
    }, [nodes.length, links]);

    const nodeMap = useMemo(() => {
        return new Map(nodes.map(node => [node.id, node]));
    }, [nodes]);

    const filteredLinks = useMemo(() => {
        const query = searchQuery.trim().toLowerCase();
        return links.filter(link => {
            if (!riskFilters[link.riskLevel]) return false;
            if (!query) return true;
            const source = nodeMap.get(link.source)?.label.toLowerCase() || '';
            const target = nodeMap.get(link.target)?.label.toLowerCase() || '';
            return source.includes(query) || target.includes(query);
        });
    }, [links, nodeMap, riskFilters, searchQuery]);

    const visibleNodeIds = useMemo(() => {
        const ids = new Set<string>();
        filteredLinks.forEach(link => {
            ids.add(link.source);
            ids.add(link.target);
        });
        return ids;
    }, [filteredLinks]);

    const filteredNodes = useMemo(() => {
        return nodes.filter(node => visibleNodeIds.has(node.id));
    }, [nodes, visibleNodeIds]);

    useEffect(() => {
        if (!selectedNode) return;
        const stillVisible = filteredNodes.some(node => node.id === selectedNode);
        if (!stillVisible) setSelectedNode(null);
    }, [filteredNodes, selectedNode]);

    useEffect(() => {
        if (!selectedLink) return;
        const stillVisible = filteredLinks.some(link => linkId(link) === selectedLink);
        if (!stillVisible) setSelectedLink(null);
    }, [filteredLinks, selectedLink]);

    const getSvgCoordinates = (clientX: number, clientY: number) => {
        const svg = svgRef.current;
        if (!svg) return null;
        const rect = svg.getBoundingClientRect();
        const svgX = ((clientX - rect.left) * WIDTH) / rect.width;
        const svgY = ((clientY - rect.top) * HEIGHT) / rect.height;
        return { svgX, svgY };
    };

    const getGraphCoordinates = (clientX: number, clientY: number) => {
        const coords = getSvgCoordinates(clientX, clientY);
        if (!coords) return null;
        return {
            x: (coords.svgX - viewTransform.x) / viewTransform.scale,
            y: (coords.svgY - viewTransform.y) / viewTransform.scale
        };
    };

    useEffect(() => {
        const handleMouseMove = (event: MouseEvent) => {
            if (draggingNode) {
                const graphCoords = getGraphCoordinates(event.clientX, event.clientY);
                if (!graphCoords) return;
                setNodes(prev =>
                    prev.map(node =>
                        node.id === draggingNode
                            ? {
                                ...node,
                                x: Math.max(20, Math.min(WIDTH - 20, graphCoords.x)),
                                y: Math.max(20, Math.min(HEIGHT - 20, graphCoords.y)),
                                vx: 0,
                                vy: 0
                            }
                            : node
                    )
                );
                return;
            }

            if (isPanning) {
                const dx = event.clientX - panStartRef.current.startX;
                const dy = event.clientY - panStartRef.current.startY;
                const widthScale = WIDTH / (svgRef.current?.getBoundingClientRect().width || WIDTH);
                const heightScale = HEIGHT / (svgRef.current?.getBoundingClientRect().height || HEIGHT);
                setViewTransform(prev => ({
                    ...prev,
                    x: panStartRef.current.x + dx * widthScale,
                    y: panStartRef.current.y + dy * heightScale
                }));
            }
        };

        const handleMouseUp = () => {
            if (draggingNode) setDraggingNode(null);
            if (isPanning) setIsPanning(false);
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [draggingNode, isPanning, viewTransform.scale, viewTransform.x, viewTransform.y]);

    const toggleRiskFilter = (risk: RiskLevel) => {
        setRiskFilters(prev => ({
            ...prev,
            [risk]: !prev[risk]
        }));
    };

    const resetView = () => {
        setViewTransform({ scale: 1, x: 0, y: 0 });
    };

    const resetFocus = () => {
        setSelectedNode(null);
        setSelectedLink(null);
        setHoveredNode(null);
    };

    const activeNode = selectedNode || hoveredNode;

    const selectedNodeData = useMemo(() => {
        if (!selectedNode) return null;
        return nodeMap.get(selectedNode) || null;
    }, [nodeMap, selectedNode]);

    const selectedNodeLinks = useMemo(() => {
        if (!selectedNode) return [];
        return filteredLinks.filter(link => link.source === selectedNode || link.target === selectedNode);
    }, [filteredLinks, selectedNode]);

    const selectedLinkData = useMemo(() => {
        if (!selectedLink) return null;
        const link = links.find(l => linkId(l) === selectedLink);
        if (!link) return null;
        const source = nodeMap.get(link.source);
        const target = nodeMap.get(link.target);
        return {
            ...link,
            sourceLabel: source?.label || link.source,
            targetLabel: target?.label || link.target
        };
    }, [links, nodeMap, selectedLink]);

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
                        Explore user-to-IP relationships, filter risk levels, and inspect attack paths.
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

            <div className="flex flex-col gap-4 mb-4">
                <div className="flex flex-wrap items-center gap-2">
                    <input
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search user or IP"
                        className="px-3 py-2 bg-slate-900/70 border border-slate-700 rounded text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    />
                    {riskOrder.map(risk => (
                        <button
                            key={risk}
                            onClick={() => toggleRiskFilter(risk)}
                            className={`px-3 py-1.5 rounded text-xs font-mono border transition-colors ${
                                riskFilters[risk]
                                    ? 'border-cyan-500/60 text-cyan-300 bg-cyan-500/10'
                                    : 'border-slate-700 text-slate-400 bg-slate-900/50'
                            }`}
                        >
                            {risk}
                        </button>
                    ))}
                    <button
                        onClick={resetFocus}
                        className="px-3 py-1.5 rounded text-xs font-mono border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors"
                    >
                        Clear Focus
                    </button>
                    <button
                        onClick={resetView}
                        className="px-3 py-1.5 rounded text-xs font-mono border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors"
                    >
                        Reset View
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[1fr_280px] gap-4">
                <div className="w-full h-[500px] bg-slate-900/50 rounded-lg overflow-hidden relative">
                    <svg
                        ref={svgRef}
                        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
                        className={`w-full h-full ${isPanning ? 'cursor-grabbing' : 'cursor-grab'}`}
                        onMouseDown={(e) => {
                            if (e.button !== 0) return;
                            panStartRef.current = {
                                x: viewTransform.x,
                                y: viewTransform.y,
                                startX: e.clientX,
                                startY: e.clientY
                            };
                            setIsPanning(true);
                        }}
                        onWheel={(e) => {
                            e.preventDefault();
                            const coords = getSvgCoordinates(e.clientX, e.clientY);
                            if (!coords) return;
                            const zoomFactor = e.deltaY < 0 ? 1.12 : 0.9;
                            const newScale = Math.max(0.6, Math.min(3, viewTransform.scale * zoomFactor));
                            const graphX = (coords.svgX - viewTransform.x) / viewTransform.scale;
                            const graphY = (coords.svgY - viewTransform.y) / viewTransform.scale;
                            setViewTransform({
                                scale: newScale,
                                x: coords.svgX - graphX * newScale,
                                y: coords.svgY - graphY * newScale
                            });
                        }}
                    >
                        <g transform={`translate(${viewTransform.x} ${viewTransform.y}) scale(${viewTransform.scale})`}>
                            {filteredLinks.map((link) => {
                                const sourceNode = nodeMap.get(link.source);
                                const targetNode = nodeMap.get(link.target);
                                if (!sourceNode || !targetNode) return null;

                                const activeLink = selectedLink === linkId(link);
                                const isConnectedToActiveNode = activeNode ? (link.source === activeNode || link.target === activeNode) : true;
                                const isDimmed = !isConnectedToActiveNode && !activeLink;
                                const strokeWidth = activeLink ? 4 : link.riskLevel === RiskLevel.CRITICAL ? 3 : 1.5;

                                return (
                                    <line
                                        key={linkId(link)}
                                        x1={sourceNode.x}
                                        y1={sourceNode.y}
                                        x2={targetNode.x}
                                        y2={targetNode.y}
                                        stroke={getLinkColor(link.riskLevel)}
                                        strokeWidth={strokeWidth}
                                        strokeOpacity={isDimmed ? 0.12 : 0.95}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setSelectedLink(linkId(link));
                                            setSelectedNode(null);
                                        }}
                                        className="cursor-pointer"
                                    />
                                );
                            })}

                            {filteredNodes.map(node => {
                                const isFocused = selectedNode === node.id || hoveredNode === node.id;
                                const isConnectedToActive = activeNode
                                    ? filteredLinks.some(link =>
                                        (link.source === activeNode || link.target === activeNode) &&
                                        (link.source === node.id || link.target === node.id)
                                    )
                                    : true;
                                const isDimmed = activeNode && !isConnectedToActive && activeNode !== node.id;

                                return (
                                    <g
                                        key={node.id}
                                        transform={`translate(${node.x},${node.y})`}
                                        onMouseEnter={() => setHoveredNode(node.id)}
                                        onMouseLeave={() => setHoveredNode(null)}
                                        onMouseDown={(e) => {
                                            e.stopPropagation();
                                            setSelectedNode(node.id);
                                            setSelectedLink(null);
                                            setDraggingNode(node.id);
                                        }}
                                        className={`transition-opacity duration-200 ${isDimmed ? 'opacity-20' : 'opacity-100'} ${draggingNode === node.id ? 'cursor-grabbing' : 'cursor-grab'}`}
                                    >
                                        {node.type === 'USER' ? (
                                            <circle
                                                r={20}
                                                fill="#06b6d4"
                                                stroke="#ecfeff"
                                                strokeWidth={isFocused ? 2.5 : 0}
                                            />
                                        ) : (
                                            <polygon
                                                points="-18,-10 0,-20 18,-10 18,10 0,20 -18,10"
                                                fill="#a855f7"
                                                stroke="#f3e8ff"
                                                strokeWidth={isFocused ? 2.5 : 0}
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
                        </g>
                    </svg>
                </div>

                <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 space-y-3">
                    <h4 className="text-sm font-semibold text-white">Investigation Panel</h4>
                    <div className="text-xs text-slate-400 font-mono">
                        <div>Nodes: {filteredNodes.length}</div>
                        <div>Paths: {filteredLinks.length}</div>
                        <div>Zoom: {(viewTransform.scale * 100).toFixed(0)}%</div>
                    </div>
                    {selectedNodeData && (
                        <div className="border border-cyan-500/30 bg-cyan-500/5 rounded p-3 space-y-2">
                            <div className="text-xs text-cyan-300 font-mono">Selected Node</div>
                            <div className="text-sm text-white break-all">{selectedNodeData.label}</div>
                            <div className="text-xs text-slate-400">Type: {selectedNodeData.type}</div>
                            <div className="text-xs text-slate-400">Connected Paths: {selectedNodeLinks.length}</div>
                            <div className="space-y-1 max-h-28 overflow-auto pr-1">
                                {selectedNodeLinks.slice(0, 8).map(link => {
                                    const peerId = link.source === selectedNodeData.id ? link.target : link.source;
                                    const peerLabel = nodeMap.get(peerId)?.label || peerId;
                                    return (
                                        <div key={linkId(link)} className="text-[11px] text-slate-300 font-mono flex justify-between gap-2">
                                            <span className="truncate">{peerLabel}</span>
                                            <span style={{ color: getLinkColor(link.riskLevel) }}>{link.riskLevel}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                    {selectedLinkData && (
                        <div className="border border-orange-500/30 bg-orange-500/5 rounded p-3 space-y-2">
                            <div className="text-xs text-orange-300 font-mono">Selected Path</div>
                            <div className="text-xs text-slate-300 break-all">{selectedLinkData.sourceLabel}</div>
                            <div className="text-[10px] text-slate-500 font-mono">TO</div>
                            <div className="text-xs text-slate-300 break-all">{selectedLinkData.targetLabel}</div>
                            <div className="text-xs font-mono" style={{ color: getLinkColor(selectedLinkData.riskLevel) }}>
                                Risk: {selectedLinkData.riskLevel}
                            </div>
                        </div>
                    )}
                    {!selectedNodeData && !selectedLinkData && (
                        <div className="text-xs text-slate-500 leading-relaxed">
                            Click a node to inspect its connected paths, click a path to inspect its risk, drag nodes to reorganize the map, drag background to pan, and use mouse wheel to zoom.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NetworkGraph;
