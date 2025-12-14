import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchStations, type Station } from '../services/api';
import { auth, db } from '../firebase';
import { doc, setDoc, arrayUnion } from 'firebase/firestore';
import { onAuthStateChanged } from 'firebase/auth';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import { Star, MapPin } from 'lucide-react';

const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const MapComponent: React.FC = () => {
    const [stations, setStations] = useState<Station[]>([]);
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, u => setUser(u));
        return unsubscribe;
    }, []);

    const addToFavorites = async (station: Station) => {
        if (!user) {
            alert("Please login to save favorites!");
            return;
        }
        try {
            const userRef = doc(db, "users", user.uid);
            await setDoc(userRef, {
                favorites: arrayUnion({
                    stop_name: station.stop_name,
                    stop_id: station.stop_id
                })
            }, { merge: true });
            alert(`Saved ${station.stop_name} to favorites!`);
        } catch (e) {
            console.error("Error saving favorite", e);
            alert("Failed to save favorite.");
        }
    };

    useEffect(() => {
        const loadStations = async () => {
            try {
                const data = await fetchStations();
                if (data.stations) {
                    setStations(data.stations);
                }
            } catch (err) {
                console.error("Failed to load map stations", err);
            }
        };
        loadStations();
    }, []);

    const position: [number, number] = [40.7580, -73.9855];

    return (
        <div className="flex flex-col h-full gap-4 animate-enter">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-[var(--text-main)]">Interactive Map</h2>
                    <p className="text-[var(--text-scnd)]">Explore stations and plan your route</p>
                </div>
            </div>

            <div className="flex-1 w-full min-h-[600px] rounded-2xl overflow-hidden border border-[var(--border-subtle)] shadow-2xl relative">
                <MapContainer center={position} zoom={13} style={{ height: '100%', width: '100%', background: '#18181b' }}>
                    <TileLayer
                        attribution='&copy; CARTO'
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    />
                    {stations.map((station) => (
                        <Marker
                            key={station.stop_id}
                            position={[
                                (station as any).stop_lat,
                                (station as any).stop_lon
                            ]}
                        >
                            <Popup>
                                <div className="p-1 min-w-[200px]">
                                    <div className="flex items-start gap-3 mb-2">
                                        <div className="bg-blue-600 p-1.5 rounded-lg">
                                            <MapPin size={16} color="white" />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-base text-gray-900">{station.stop_name}</h3>
                                            <p className="text-xs text-gray-500 font-medium">
                                                Lines: <span className="text-blue-600">{(station as any).routes?.join(', ')}</span>
                                            </p>
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => addToFavorites(station)}
                                        className="w-full mt-2 flex items-center justify-center gap-2 bg-gray-900 text-white text-xs font-semibold py-2 rounded-lg hover:bg-black transition-colors"
                                    >
                                        <Star size={12} />
                                        Add to Favorites
                                    </button>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
        </div>
    );
};

export default MapComponent;
