import requests
import json
from datetime import datetime
import time
import logging
from google.transit import gtfs_realtime_pb2
from config.logging_config import api_logger

logger = logging.getLogger(__name__)


class LIRRService:
    """
    Service for Long Island Rail Road (LIRR) real-time data
    API Documentation: https://api.mta.info/#/subwayRealTimeFeeds
    """
    
    # LIRR GTFS Realtime feed
    LIRR_FEED_URL = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/lirr%2Fgtfs-lirr'
    LIRR_ALERTS_URL = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/lirr%2Fgtfs-lirr-alerts'
    
    def __init__(self, api_key=None):
        self.session = requests.Session()
        
        # LIRR stations (major ones)
        self.lirr_stations = self._load_lirr_stations()
        
        logger.info("LIRR service initialized")
    
    def _load_lirr_stations(self):
        """Load LIRR station data"""
        # Major LIRR stations
        return {
            'Penn Station': {'id': '237', 'name': 'Penn Station', 'lines': ['All']},
            'Jamaica': {'id': '139', 'name': 'Jamaica', 'lines': ['All']},
            'Hicksville': {'id': '128', 'name': 'Hicksville', 'lines': ['Ronkonkoma', 'Port Jefferson', 'Oyster Bay']},
            'Babylon': {'id': '18', 'name': 'Babylon', 'lines': ['Babylon']},
            'Ronkonkoma': {'id': '211', 'name': 'Ronkonkoma', 'lines': ['Ronkonkoma']},
            'Port Jefferson': {'id': '199', 'name': 'Port Jefferson', 'lines': ['Port Jefferson']},
            'Huntington': {'id': '134', 'name': 'Huntington', 'lines': ['Port Jefferson']},
            'Long Beach': {'id': '153', 'name': 'Long Beach', 'lines': ['Long Beach']},
            'Far Rockaway': {'id': '101', 'name': 'Far Rockaway', 'lines': ['Far Rockaway']},
            'Hempstead': {'id': '124', 'name': 'Hempstead', 'lines': ['Hempstead']},
            'Oyster Bay': {'id': '188', 'name': 'Oyster Bay', 'lines': ['Oyster Bay']},
            'Port Washington': {'id': '200', 'name': 'Port Washington', 'lines': ['Port Washington']},
            'Atlantic Terminal': {'id': '8', 'name': 'Atlantic Terminal', 'lines': ['All']},
            'Mineola': {'id': '167', 'name': 'Mineola', 'lines': ['All']},
            'Freeport': {'id': '109', 'name': 'Freeport', 'lines': ['Babylon']},
        }
    
    def find_station(self, query):
        """Find LIRR station by name (fuzzy matching)"""
        from rapidfuzz import fuzz, process
        
        query_lower = query.lower()
        
        # Try exact match first
        for station_name, station_data in self.lirr_stations.items():
            if query_lower in station_name.lower() or station_name.lower() in query_lower:
                return station_data
        
        # Fuzzy match
        station_names = list(self.lirr_stations.keys())
        result = process.extractOne(
            query,
            station_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=70
        )
        
        if result:
            return self.lirr_stations[result[0]]
        
        return None
    
    def get_train_arrivals(self, station_name, limit=5):
        """
        Get real-time LIRR train arrivals at a station
        
        Args:
            station_name: Name of LIRR station
            limit: Number of arrivals to return
        
        Returns:
            List of upcoming train arrivals
        """
        start_time = time.time()
        
        try:
            
            station = self.find_station(station_name)
            if not station:
                return {'error': f'Could not find LIRR station: {station_name}'}
            
            logger.info(f"Fetching LIRR arrivals for {station['name']}")
            
            response = self.session.get(self.LIRR_FEED_URL, timeout=10)
            response_time = time.time() - start_time
            
            api_logger.log_api_call(
                service_name='LIRR_GTFS_REALTIME',
                endpoint=self.LIRR_FEED_URL,
                method='GET',
                response_status=response.status_code,
                response_time=response_time
            )
            
            response.raise_for_status()
            
            # Parse GTFS Realtime protobuf
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            arrivals = []
            station_id = station['id']
            
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    trip = entity.trip_update
                    
                    for stop_time_update in trip.stop_time_update:
                        if station_id in stop_time_update.stop_id:
                            # Get arrival time
                            if stop_time_update.HasField('arrival'):
                                arrival_timestamp = stop_time_update.arrival.time
                            elif stop_time_update.HasField('departure'):
                                arrival_timestamp = stop_time_update.departure.time
                            else:
                                continue
                            
                            arrival_datetime = datetime.fromtimestamp(arrival_timestamp)
                            minutes_away = int((arrival_datetime - datetime.now()).total_seconds() / 60)
                            
                            if minutes_away < 0:  # Skip past trains
                                continue
                            
                            # Get destination from trip headsign
                            destination = trip.trip.trip_headsign if hasattr(trip.trip, 'trip_headsign') else 'Unknown'
                            
                            arrivals.append({
                                'destination': destination,
                                'arrival_time': arrival_datetime.strftime('%I:%M %p'),
                                'minutes_away': minutes_away,
                                'track': stop_time_update.platform_id if hasattr(stop_time_update, 'platform_id') else 'TBD'
                            })
            
            # Sort by arrival time
            arrivals.sort(key=lambda x: x['minutes_away'])
            
            logger.info(f"Found {len(arrivals)} LIRR arrivals at {station['name']}")
            
            return arrivals[:limit]
            
        except requests.RequestException as e:
            response_time = time.time() - start_time
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Failed to fetch LIRR arrivals: {error_msg}")
            
            api_logger.log_api_call(
                service_name='LIRR_GTFS_REALTIME',
                endpoint=self.LIRR_FEED_URL,
                method='GET',
                response_time=response_time,
                error=error_msg
            )
            
            return {'error': error_msg}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    def get_service_alerts(self):
        """
        Get LIRR service alerts and delays
        
        Returns:
            List of active service alerts
        """
        start_time = time.time()
        
        try:
            
            logger.info("Fetching LIRR service alerts")
            
            response = self.session.get(self.LIRR_ALERTS_URL, timeout=10)
            response_time = time.time() - start_time
            
            api_logger.log_api_call(
                service_name='LIRR_SERVICE_ALERTS',
                endpoint=self.LIRR_ALERTS_URL,
                method='GET',
                response_status=response.status_code,
                response_time=response_time
            )
            
            response.raise_for_status()
            
            # Parse GTFS Realtime alerts
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            alerts = []
            for entity in feed.entity:
                if entity.HasField('alert'):
                    alert = entity.alert
                    
                    header = alert.header_text.translation[0].text if alert.header_text.translation else "No header"
                    description = alert.description_text.translation[0].text if alert.description_text.translation else ""
                    
                    # Get affected lines
                    affected_lines = []
                    for informed_entity in alert.informed_entity:
                        if hasattr(informed_entity, 'route_id'):
                            affected_lines.append(informed_entity.route_id)
                    
                    alerts.append({
                        'header': header,
                        'description': description,
                        'affected_lines': list(set(affected_lines))  # Remove duplicates
                    })
            
            logger.info(f"Found {len(alerts)} LIRR service alerts")
            return alerts
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Failed to fetch LIRR alerts: {str(e)}")
            
            api_logger.log_api_call(
                service_name='LIRR_SERVICE_ALERTS',
                endpoint=self.LIRR_ALERTS_URL,
                method='GET',
                response_time=response_time,
                error=str(e)
            )
            
            return {'error': str(e)}
    
    def get_lines_at_station(self, station_name):
        """Get which LIRR lines serve a station"""
        station = self.find_station(station_name)
        if station:
            return station['lines']
        return []
