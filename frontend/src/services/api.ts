import axios from 'axios';

// The proxy in vite.config.ts forwards /api requests to localhost:5000
const api = axios.create({
    baseURL: '/api',
});

export interface Station {
    stop_id: string;
    stop_name: string;
    gtfs_stop_ids: string[];
    location: [number, number]; // [lat, lon] usually, or handle as needed
}

export interface Alert {
    header: string;
    description: string;
    affected_routes: string[];
}

export interface Arrival {
    train_line: string;
    direction: string;
    arrival_time: string;
    minutes_away: number;
    stop_id: string;
}

export const fetchStations = async (line?: string) => {
    try {
        const response = await api.get('/stations', { params: { line } });
        return response.data;
    } catch (error) {
        console.warn("Using mock stations due to API error", error);
        // Fallback mock since backend might not be running yet or empty
        return {
            stations: [
                { stop_name: "Times Sq-42 St", stop_id: "TSQ", stop_lat: 40.7553, stop_lon: -73.9874, routes: ['1', '2', '3', '7', 'N', 'Q', 'R', 'W'] },
                { stop_name: "Grand Central-42 St", stop_id: "GCT", stop_lat: 40.7527, stop_lon: -73.9772, routes: ['4', '5', '6', '7'] },
                { stop_name: "Union Sq-14 St", stop_id: "USQ", stop_lat: 40.7357, stop_lon: -73.9906, routes: ['L', 'N', 'Q', 'R', 'W', '4', '5', '6'] },
            ]
        };
    }
};

export const fetchAlerts = async (line?: string) => {
    try {
        const response = await api.get('/alerts', { params: { line } });
        return response.data.alerts || [];
    } catch (error) {
        return [];
    }
};

export const fetchElevatorStatus = async (station: string) => {
    const response = await api.get('/elevator-status', { params: { station } });
    return response.data;
};

export const fetchArrivals = async (station: string, line: string) => {
    const response = await api.get('/arrivals', { params: { station, line } });
    return response.data;
};

export const fetchLiveTrains = async (line?: string) => {
    const response = await api.get('/live-trains', { params: { line } });
    return response.data;
};

export const sendChatMessage = async (message: string) => {
    // Note: Session management might need to be handled carefully with cookies or headers
    // The Flask app uses server-side sessions, so just sending credentials/cookies implies it works.
    // However, for API calls axios handles cookies if configured.
    const response = await api.post('/chat', { message });
    return response.data;
};

export default api;
