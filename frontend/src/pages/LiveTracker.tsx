import React, { useState } from 'react';
import { Search, ChevronRight, Navigation, Loader } from 'lucide-react';
import { fetchStations, fetchArrivals, type Station, type Arrival } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

const LiveTracker: React.FC = () => {
    const [query, setQuery] = useState('');
    const [mode, setMode] = useState<'home' | 'line' | 'station'>('home');
    const [lineData, setLineData] = useState<{ id: string, stations: Station[] } | null>(null);
    const [stationData, setStationData] = useState<{ station: Station, arrivals: Arrival[] } | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const popularLines = ['1', '2', '3', '4', '5', '6', '7', 'A', 'C', 'E', 'B', 'D', 'F', 'M', 'N', 'Q', 'R', 'L'];

    const executeSearch = async (searchTerm: string) => {
        if (!searchTerm.trim()) return;

        setError('');
        setLoading(true);
        const input = searchTerm.trim().toUpperCase();
        setQuery(input); // Sync state

        // 1. Check if it's a line
        if (/^[A-Z0-9]$/.test(input) || popularLines.includes(input)) {
            try {
                const data = await fetchStations(input);
                if (data.stations && data.stations.length > 0) {
                    setLineData({ id: input, stations: data.stations });
                    setMode('line');
                } else {
                    setError(`No stations found for line ${input}`);
                }
            } catch (err) {
                setError('Failed to fetch line info');
            }
        }
        // 2. Treat as Station Name
        else {
            try {
                const data = await fetchStations();
                const allStations: Station[] = data.stations || [];

                const matches = allStations.filter(s =>
                    s.stop_name.toLowerCase().includes(input.toLowerCase())
                );

                if (matches.length > 0) {
                    const bestMatch = matches.find(s => s.stop_name.toLowerCase() === input.toLowerCase()) || matches[0];
                    await viewStation(bestMatch);
                } else {
                    setError(`No station found matching "${input}"`);
                }
            } catch (err) {
                setError('Failed to search stations');
            }
        }
        setLoading(false);
    };

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        executeSearch(query);
    };

    const viewStation = async (station: Station) => {
        setLoading(true);
        try {
            const allArrivals: Arrival[] = [];
            // Run in parallel
            await Promise.all((station as any).routes?.map(async (r: string) => {
                const res = await fetchArrivals(station.stop_name || '', r);
                if (res.arrivals) allArrivals.push(...res.arrivals);
            }) || []);

            // Sort by time
            allArrivals.sort((a, b) => a.minutes_away - b.minutes_away);

            setStationData({ station, arrivals: allArrivals });
            setMode('station');
        } catch (err) {
            setError('Failed to load arrivals');
        }
        setLoading(false);
    };

    const goHome = () => {
        setMode('home');
        setQuery('');
        setLineData(null);
        setStationData(null);
        setError('');
    };

    // Filter arrivals by direction
    const uptownArrivals = stationData?.arrivals.filter(a =>
        a.direction.includes('Uptown') || a.direction.includes('Queens') || a.direction.includes('Bronx') || a.direction.includes('North')
    ) || [];

    const downtownArrivals = stationData?.arrivals.filter(a =>
        !a.direction.includes('Uptown') && !a.direction.includes('Queens') && !a.direction.includes('Bronx') && !a.direction.includes('North')
    ) || [];

    const ArrivalCard = ({ arr }: { arr: Arrival }) => (
        <div className="bg-[var(--bg-card)] p-4 rounded-xl border border-[var(--border-subtle)] flex items-center justify-between hover:border-[var(--border-highlight)] transition-colors">
            <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-[var(--bg-app)] flex items-center justify-center font-bold text-lg border border-[var(--border-subtle)] shadow-sm">
                    {arr.train_line}
                </div>
                <div>
                    <p className="font-semibold">{arr.direction}</p>
                    <p className="text-xs text-[var(--text-scnd)]">
                        {arr.direction.includes('Uptown') || arr.direction.includes('Bronx') ? 'Northbound' : 'Southbound'}
                    </p>
                </div>
            </div>
            <div className="text-right">
                <div className="text-xl font-bold text-blue-400">
                    {arr.minutes_away} <span className="text-sm text-[var(--text-scnd)] font-normal">min</span>
                </div>
                <div className="text-xs text-[var(--text-scnd)]">{arr.arrival_time}</div>
            </div>
        </div>
    );

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-enter min-h-[60vh]">
            <header className="text-center space-y-2">
                <h1 className="text-3xl font-bold flex justify-center items-center gap-2 text-[var(--text-main)]">
                    <Navigation className="text-blue-500" />
                    Live Tracker
                </h1>
                <p className="text-[var(--text-scnd)]">Find your train and see it coming.</p>
            </header>

            {/* Search Bar */}
            <form onSubmit={handleSearchSubmit} className="relative">
                <input
                    type="text"
                    placeholder="Search Line (e.g., Q) or Station (e.g., Union Sq)..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] text-lg shadow-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />

                {loading ? (
                    <Loader className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-500 animate-spin" size={20} />
                ) : (
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-scnd)]" size={20} />
                )}
            </form>

            <AnimatePresence mode="wait">
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 bg-red-900/20 border border-red-500/30 text-red-400 rounded-xl text-center"
                    >
                        {error}
                    </motion.div>
                )}

                {/* MODE: HOME (Suggestions) */}
                {mode === 'home' && !loading && (
                    <motion.div
                        key="home"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <h3 className="text-sm font-semibold text-[var(--text-scnd)] mb-3">Popular Lines</h3>
                        <div className="flex flex-wrap gap-2">
                            {popularLines.map(line => (
                                <button
                                    key={line}
                                    onClick={() => executeSearch(line)}
                                    className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] hover:scale-110 hover:border-blue-500 transition-all cursor-pointer"
                                >
                                    {line}
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* MODE: LINE VIEW */}
                {mode === 'line' && lineData && (
                    <motion.div
                        key="line"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-subtle)] overflow-hidden"
                    >
                        <div className="p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-app)]/50 flex items-center justify-between">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <span className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm">
                                    {lineData.id}
                                </span>
                                {lineData.id} Line Stations
                            </h2>
                            <button onClick={goHome} className="text-sm text-[var(--text-scnd)] hover:text-white">Close</button>
                        </div>
                        <div className="max-h-[600px] overflow-y-auto">
                            {lineData.stations.map((s, _idx) => (
                                <button
                                    key={s.stop_id}
                                    onClick={() => viewStation(s)}
                                    className="w-full text-left p-4 border-b border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)] flex items-center justify-between group transition-colors"
                                >
                                    <span className="font-medium group-hover:text-blue-400 transition-colors">
                                        {s.stop_name}
                                    </span>
                                    <ChevronRight size={16} className="text-[var(--text-scnd)]" />
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* MODE: STATION VIEW */}
                {mode === 'station' && stationData && (
                    <motion.div
                        key="station"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-6"
                    >
                        <button onClick={() => lineData ? setMode('line') : goHome()} className="text-sm text-[var(--text-scnd)] hover:text-blue-400 flex items-center gap-1">
                            ← Back
                        </button>

                        <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-subtle)] overflow-hidden p-6 text-center shadow-lg">
                            <h2 className="text-3xl font-bold mb-2 text-white">{stationData.station.stop_name}</h2>
                            <div className="flex justify-center gap-2 mt-2">
                                {(stationData.station as any).routes?.map((r: string) => (
                                    <span key={r} className="px-3 py-1 rounded-full text-sm font-bold bg-[#1A1A1A] border border-gray-700 shadow-inner">
                                        {r}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Split View for Arrivals */}
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Uptown / Northbound */}
                            <div className="space-y-3">
                                <h3 className="font-bold flex items-center gap-2 text-lg text-[var(--text-main)] border-b border-[var(--border-subtle)] pb-2 mb-2">
                                    <span className="text-blue-500">↑</span> Uptown / Queens
                                </h3>
                                {uptownArrivals.length > 0 ? (
                                    uptownArrivals.map((arr, i) => <ArrivalCard key={i} arr={arr} />)
                                ) : (
                                    <p className="text-[var(--text-scnd)] italic text-sm py-4 text-center bg-[var(--bg-card)] rounded-lg">No upcoming trains</p>
                                )}
                            </div>

                            {/* Downtown / Southbound */}
                            <div className="space-y-3">
                                <h3 className="font-bold flex items-center gap-2 text-lg text-[var(--text-main)] border-b border-[var(--border-subtle)] pb-2 mb-2">
                                    <span className="text-amber-500">↓</span> Downtown / Brooklyn
                                </h3>
                                {downtownArrivals.length > 0 ? (
                                    downtownArrivals.map((arr, i) => <ArrivalCard key={i} arr={arr} />)
                                ) : (
                                    <p className="text-[var(--text-scnd)] italic text-sm py-4 text-center bg-[var(--bg-card)] rounded-lg">No upcoming trains</p>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default LiveTracker;
