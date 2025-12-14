import React, { useEffect, useState } from 'react';
import { fetchAlerts, type Alert } from '../services/api';
import { AlertTriangle, CheckCircle, RefreshCcw } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard: React.FC = () => {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

    const loadData = async () => {
        setLoading(true);
        const data = await fetchAlerts();
        setAlerts(data);
        setLoading(false);
    };

    useEffect(() => {
        loadData();
    }, []);

    // Line Groups
    const lines = [
        { id: '1', color: 'var(--line-123)' }, { id: '2', color: 'var(--line-123)' }, { id: '3', color: 'var(--line-123)' },
        { id: '4', color: 'var(--line-456)' }, { id: '5', color: 'var(--line-456)' }, { id: '6', color: 'var(--line-456)' },
        { id: '7', color: 'var(--line-7)' },
        { id: 'A', color: 'var(--line-ACE)' }, { id: 'C', color: 'var(--line-ACE)' }, { id: 'E', color: 'var(--line-ACE)' },
        { id: 'B', color: 'var(--line-BDFM)' }, { id: 'D', color: 'var(--line-BDFM)' }, { id: 'F', color: 'var(--line-BDFM)' }, { id: 'M', color: 'var(--line-BDFM)' },
        { id: 'N', color: 'var(--line-NQRW)' }, { id: 'Q', color: 'var(--line-NQRW)' }, { id: 'R', color: 'var(--line-NQRW)' }, { id: 'W', color: 'var(--line-NQRW)' },
        { id: 'G', color: 'var(--line-G)' },
        { id: 'L', color: 'var(--line-L)' },
        { id: 'J', color: 'var(--line-JZ)' }, { id: 'Z', color: 'var(--line-JZ)' },
        { id: 'S', color: 'var(--line-S)' }
    ];

    const getStatus = (lineId: string) => {
        const lineAlerts = alerts.filter(a => a.affected_routes.includes(lineId));
        return {
            hasDelay: lineAlerts.length > 0,
            count: lineAlerts.length
        };
    };

    return (
        <div className="space-y-8 animate-enter">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-[var(--text-main)]">System Status</h1>
                    <p className="text-[var(--text-scnd)]">Live service status across the network</p>
                </div>
                <button
                    onClick={loadData}
                    className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-lg text-sm hover:bg-[var(--bg-card-hover)] transition-colors text-[var(--text-scnd)] hover:text-[var(--text-main)] self-start md:self-auto"
                >
                    <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
                    Refresh
                </button>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
                {lines.map((line) => {
                    const { hasDelay } = getStatus(line.id);
                    return (
                        <div
                            key={line.id}
                            className={`
                                relative p-4 rounded-xl border transition-all flex flex-col items-center justify-center gap-3 h-32
                                ${hasDelay
                                    ? 'bg-red-900/10 border-red-500/30'
                                    : 'bg-[var(--bg-card)] border-[var(--border-subtle)] hover:border-[var(--border-highlight)] hover:bg-[var(--bg-card-hover)]'
                                }
                            `}
                        >
                            {/* Line Bubble */}
                            <div
                                className="w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold text-white shadow-lg"
                                style={{ backgroundColor: line.color }}
                            >
                                {line.id}
                            </div>

                            {/* Status Text - Centered */}
                            <div className="flex items-center gap-1.5">
                                {hasDelay ? (
                                    <>
                                        <AlertTriangle size={14} className="text-red-500" />
                                        <span className="text-xs font-semibold text-red-500 uppercase tracking-wide">Delays</span>
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle size={14} className="text-[var(--success)]" />
                                        <span className="text-xs font-semibold text-[var(--success)] uppercase tracking-wide">Good</span>
                                    </>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Alerts Section - Two Column Layout for better reading */}
            <div className="mt-8">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-[var(--warning)]">
                    <AlertTriangle size={20} />
                    Active Alerts
                </h2>

                {loading ? (
                    <div className="text-[var(--text-scnd)]">Checking for alerts...</div>
                ) : alerts.length > 0 ? (
                    <div className="grid md:grid-cols-2 gap-4">
                        {alerts.map((alert, idx) => (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                key={idx}
                                className="p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] hover:border-[var(--warning)]/50 transition-colors"
                            >
                                <div className="flex flex-wrap gap-2 mb-3">
                                    {alert.affected_routes.map((r, i) => (
                                        <span key={`${r}-${i}`} className="px-2 py-1 text-xs font-bold rounded bg-[var(--bg-card-hover)] text-[var(--text-main)] border border-[var(--border-subtle)]">
                                            {r}
                                        </span>
                                    ))}
                                </div>
                                <h3 className="font-semibold text-[var(--text-main)] mb-2 leading-tight">{alert.header}</h3>
                                <p className="text-sm text-[var(--text-scnd)] line-clamp-3">{alert.description}</p>
                            </motion.div>
                        ))}
                    </div>
                ) : (
                    <div className="p-6 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] text-center text-[var(--text-scnd)]">
                        No active service alerts reported at this time.
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
