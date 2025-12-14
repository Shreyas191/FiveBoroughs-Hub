import React, { useState, useEffect } from 'react';
import { fetchElevatorStatus } from '../services/api';
import { Accessibility as AccessIcon, CheckCircle, XCircle, ArrowUpFromLine, AlertTriangle } from 'lucide-react';

const AccessibilityPage: React.FC = () => {
    const [statuses, setStatuses] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const hubs = [
        "Grand Central-42 St",
        "Times Sq-42 St",
        "34 St-Penn Station",
        "Fulton St",
        "Atlantic Av-Barclays Ctr",
        "Jay St-MetroTech",
        "Jackson Hts-Roosevelt Av"
    ];

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            const promises = hubs.map(h => fetchElevatorStatus(h));
            const results = await Promise.all(promises);
            setStatuses(results);
            setLoading(false);
        };
        load();
    }, []);

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8 animate-enter">
            <header>
                <h1 className="text-3xl font-bold mb-2 flex items-center gap-3 text-[var(--text-main)]">
                    <AccessIcon className="text-blue-500" size={32} />
                    Accessibility Hub
                </h1>
                <p className="text-[var(--text-scnd)]">Live elevator & escalator status for major accessible stations.</p>
            </header>

            {loading ? (
                <div className="text-[var(--text-scnd)] text-center py-10">Loading accessibility status...</div>
            ) : (
                <div className="grid gap-6">
                    {statuses.map((item, idx) => {
                        const stationName = item.station || hubs[idx];
                        const equipmentList = item.status?.equipment || [];
                        const hasIssue = item.status?.out_of_service > 0;
                        const total = item.status?.total_equipment || 0;

                        return (
                            <div key={idx} className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-xl overflow-hidden shadow-sm hover:border-[var(--border-highlight)] transition-colors">
                                <div className="p-6 border-b border-[var(--border-subtle)] flex flex-wrap justify-between items-center gap-4 bg-[var(--bg-app)]/50">
                                    <div>
                                        <h3 className="text-xl font-bold text-[var(--text-main)]">{stationName}</h3>
                                        <p className="text-sm text-[var(--text-scnd)] mt-1">
                                            {total} Units Monitored
                                        </p>
                                    </div>

                                    <div>
                                        {hasIssue ? (
                                            <span className="flex items-center gap-2 text-red-400 bg-red-900/20 px-4 py-2 rounded-full border border-red-500/30 text-sm font-medium">
                                                <XCircle size={16} /> {item.status?.out_of_service} Outages
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-2 text-[var(--success)] bg-green-900/20 px-4 py-2 rounded-full border border-green-500/30 text-sm font-medium">
                                                <CheckCircle size={16} /> Fully Operational
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <div className="p-6 space-y-4">
                                    {equipmentList.length > 0 ? (
                                        <div className="grid gap-3 sm:grid-cols-2">
                                            {equipmentList.map((eq: any, i: number) => (
                                                <div
                                                    key={i}
                                                    className={`
                                                        p-3 rounded-lg border text-sm flex gap-3
                                                        ${eq.is_out_of_service
                                                            ? 'bg-red-900/10 border-red-500/20'
                                                            : 'bg-[var(--bg-app)] border-[var(--border-subtle)]'
                                                        }
                                                    `}
                                                >
                                                    <div className={`mt-0.5 ${eq.is_out_of_service ? 'text-red-400' : 'text-[var(--text-scnd)]'}`}>
                                                        {eq.is_out_of_service ? <AlertTriangle size={16} /> : <ArrowUpFromLine size={16} />}
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <span className={`font-semibold ${eq.is_out_of_service ? 'text-red-400' : 'text-[var(--text-main)]'}`}>
                                                                {eq.equipment_type === 'EL' ? 'Elevator' : 'Escalator'} {eq.equipment_id}
                                                            </span>
                                                            {!eq.is_out_of_service && (
                                                                <span className="text-[10px] uppercase tracking-wider text-[var(--success)] bg-green-900/20 px-1.5 py-0.5 rounded border border-green-500/30">
                                                                    Active
                                                                </span>
                                                            )}
                                                        </div>
                                                        <p className="text-[var(--text-scnd)] leading-snug">{eq.serving}</p>
                                                        {eq.is_out_of_service && (
                                                            <p className="text-red-400 mt-2 font-medium text-xs">
                                                                Status: Temporarily Out of Service
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-[var(--text-scnd)] italic">No equipment data available.</p>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default AccessibilityPage;
