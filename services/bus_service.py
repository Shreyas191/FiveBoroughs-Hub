import requests
from datetime import datetime
from google.transit import gtfs_realtime_pb2

class BusService:
    """Service for MTA Bus real-time data"""
    
    # Note: Bus APIs require an API key
    BASE_URL = 'https://gtfsrt.prod.obanyc.com'
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.session = requests.Session()
    
    def get_trip_updates(self, route=None):
        """Get bus trip updates"""
        if not self.api_key:
            return {'error': 'Bus API key required. Get one from bustime.mta.info/wiki/Developers'}
        
        try:
            url = f'{self.BASE_URL}/tripUpdates'
            params = {'key': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            updates = []
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    trip = entity.trip_update.trip
                    
                    # Filter by route if specified
                    if route and hasattr(trip, 'route_id'):
                        if not trip.route_id.startswith(route):
                            continue
                    
                    for stop_time_update in entity.trip_update.stop_time_update:
                        if stop_time_update.HasField('arrival'):
                            arrival_time = stop_time_update.arrival.time
                            arrival_datetime = datetime.fromtimestamp(arrival_time)
                            minutes_away = int((arrival_datetime - datetime.now()).total_seconds() / 60)
                            
                            updates.append({
                                'route': trip.route_id if hasattr(trip, 'route_id') else 'Unknown',
                                'stop_id': stop_time_update.stop_id,
                                'arrival_time': arrival_datetime.strftime('%I:%M %p'),
                                'minutes_away': max(0, minutes_away)
                            })
            
            updates.sort(key=lambda x: x['minutes_away'])
            return updates[:10]
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_vehicle_positions(self, route=None):
        """Get real-time bus positions"""
        if not self.api_key:
            return {'error': 'Bus API key required'}
        
        try:
            url = f'{self.BASE_URL}/vehiclePositions'
            params = {'key': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            vehicles = []
            for entity in feed.entity:
                if entity.HasField('vehicle'):
                    vehicle = entity.vehicle
                    
                    if route and hasattr(vehicle.trip, 'route_id'):
                        if not vehicle.trip.route_id.startswith(route):
                            continue
                    
                    vehicles.append({
                        'vehicle_id': vehicle.vehicle.id if hasattr(vehicle, 'vehicle') else 'Unknown',
                        'route': vehicle.trip.route_id if hasattr(vehicle.trip, 'route_id') else 'Unknown',
                        'latitude': vehicle.position.latitude if hasattr(vehicle, 'position') else None,
                        'longitude': vehicle.position.longitude if hasattr(vehicle, 'position') else None,
                        'bearing': vehicle.position.bearing if hasattr(vehicle.position, 'bearing') else None
                    })
            
            return vehicles
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_alerts(self, route=None):
        """Get bus service alerts"""
        if not self.api_key:
            return {'error': 'Bus API key required'}
        
        try:
            url = f'{self.BASE_URL}/alerts'
            params = {'key': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            alerts = []
            for entity in feed.entity:
                if entity.HasField('alert'):
                    alert = entity.alert
                    
                    # Filter by route if specified
                    if route:
                        route_match = False
                        for informed_entity in alert.informed_entity:
                            if hasattr(informed_entity, 'route_id') and informed_entity.route_id.startswith(route):
                                route_match = True
                                break
                        if not route_match:
                            continue
                    
                    header = alert.header_text.translation[0].text if alert.header_text.translation else "No header"
                    description = alert.description_text.translation[0].text if alert.description_text.translation else "No description"
                    
                    alerts.append({
                        'header': header,
                        'description': description,
                        'affected_routes': [ie.route_id for ie in alert.informed_entity if hasattr(ie, 'route_id')]
                    })
            
            return alerts
            
        except Exception as e:
            return {'error': str(e)}
