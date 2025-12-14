import requests
from datetime import datetime
import re
import json
import os
from google.transit import gtfs_realtime_pb2
from rapidfuzz import fuzz, process

class MTAService:
    """Enhanced service for interacting with MTA APIs"""
    
    FEED_URLS = {
        'ace': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace',
        'bdfm': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm',
        'g': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g',
        'jz': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz',
        'nqrw': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw',
        'l': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l',
        '1234567': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs',
        'si': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si'
    }
    
    ALERTS_URL = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts'
    
    STATION_ALIASES = {
        'times sq': 'Times Sq',
        'times square': 'Times Sq',
        'time square': 'Times Sq',
        'penn station': 'Penn Station',
        'penn sta': 'Penn Station',
        'grand central': 'Grand Central',
        'port authority': 'Port Authority',
        'columbus circle': 'Columbus Circle',
        'union sq': 'Union Sq',
        'union square': 'Union Sq',
        'herald sq': 'Herald Sq',
        'herald square': 'Herald Sq',
        'world trade': 'World Trade',
        'wtc': 'World Trade',
        'barclays': 'Barclays',
        'atlantic': 'Atlantic',
        'jay st': 'Jay St',
        'brooklyn bridge': 'Brooklyn Bridge',
        'city hall': 'City Hall',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.stations = self._load_stations()
        self.route_info = self._load_route_info()
        # Pre-compute normalized station names for faster matching
        self._build_station_index()
    
    def _load_stations(self):
        """Load all subway stations from JSON file"""
        try:
            stations_file = os.path.join('data', 'subway_stations.json')
            with open(stations_file, 'r') as f:
                data = json.load(f)
                return data.get('stations', [])
        except FileNotFoundError:
            print("Warning: subway_stations.json not found. Using fallback data.")
            return []
    
    def _load_route_info(self):
        """Load route information"""
        try:
            route_file = os.path.join('data', 'route_info.json')
            with open(route_file, 'r') as f:
                data = json.load(f)
                return data.get('routes', {})
        except FileNotFoundError:
            return {}
    
    def _build_station_index(self):
        """Build index of normalized station names for faster matching"""
        self.station_index = {}
        for station in self.stations:
            # Store both original and normalized versions
            normalized = self._normalize_station_name(station['stop_name'])
            self.station_index[normalized] = station
            
            # Also index by major keywords
            keywords = self._extract_keywords(station['stop_name'])
            for keyword in keywords:
                if keyword not in self.station_index:
                    self.station_index[keyword] = []
                if isinstance(self.station_index[keyword], list):
                    self.station_index[keyword].append(station)
                else:
                    self.station_index[keyword] = [self.station_index[keyword], station]
    
    def _normalize_station_name(self, name):
        """
        Normalize station name for better matching
        - Convert to lowercase
        - Remove special characters
        - Standardize abbreviations
        - Remove extra whitespace
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Replace common abbreviations and variations
        replacements = {
            'street': 'st',
            'avenue': 'ave',
            'boulevard': 'blvd',
            'parkway': 'pkwy',
            'square': 'sq',
            'station': 'st',
            'center': 'ctr',
            'centre': 'ctr',
            'saint': 'st',
            'fort': 'ft',
            'mount': 'mt',
            'plaza': 'plz',
            'and': '&',
            '-': ' ',  # Convert hyphens to spaces for better token matching
            '/': ' ',  # Convert slashes to spaces
        }
        
        for old, new in replacements.items():
            normalized = re.sub(r'\b' + old + r'\b', new, normalized)
        
        # Remove special characters except spaces and numbers
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _extract_keywords(self, name):
        """Extract important keywords from station name"""
        normalized = self._normalize_station_name(name)
        
        # Remove common filler words
        stop_words = {'the', 'at', 'of', 'and', 'or', 'in', 'on', 'to', 'a', 'an'}
        keywords = [w for w in normalized.split() if w not in stop_words and len(w) > 1]
        
        return keywords
    
    def find_station(self, query):
        """
        Find station using intelligent fuzzy matching with multiple strategies
        Handles variations like:
        - "times sq 42nd st" -> "Times Sq-42 St"
        - "59th street" -> "59 St-Columbus Circle" or "Lexington Ave/59 St"
        - "penn station" -> "34 St-Penn Station"
        """
        if not self.stations or not query:
            return None
        
        # Normalize the query
        normalized_query = self._normalize_station_name(query)
        
        # Strategy 1: Check for known aliases
        for alias, standard in self.STATION_ALIASES.items():
            if alias in normalized_query:
                normalized_query = normalized_query.replace(alias, self._normalize_station_name(standard))
        
        # Strategy 2: Try exact match on normalized names
        if normalized_query in self.station_index:
            result = self.station_index[normalized_query]
            if isinstance(result, dict):
                return result
        
        # Strategy 3: Try keyword-based matching for partial queries
        query_keywords = self._extract_keywords(query)
        keyword_matches = []
        
        for station in self.stations:
            station_keywords = self._extract_keywords(station['stop_name'])
            # Check if all query keywords are in station keywords
            if all(any(qk in sk for sk in station_keywords) for qk in query_keywords):
                keyword_matches.append(station)
        
        # If we found keyword matches, use fuzzy matching on those
        if keyword_matches:
            station_names = [s['stop_name'] for s in keyword_matches]
            result = process.extractOne(
                query,
                station_names,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=60  # Lower threshold for keyword matches
            )
            if result:
                for station in keyword_matches:
                    if station['stop_name'] == result[0]:
                        return station
        
        # Strategy 4: Fuzzy match with token_sort_ratio (ignores word order)
        station_names = [s['stop_name'] for s in self.stations]
        result = process.extractOne(
            query,
            station_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=70
        )
        
        if result:
            for station in self.stations:
                if station['stop_name'] == result[0]:
                    return station
        
        # Strategy 5: More lenient partial matching for very short queries
        if len(query.split()) <= 2:
            result = process.extractOne(
                normalized_query,
                [self._normalize_station_name(s['stop_name']) for s in self.stations],
                scorer=fuzz.partial_ratio,
                score_cutoff=80
            )
            
            if result:
                # Find original station
                for station in self.stations:
                    if self._normalize_station_name(station['stop_name']) == result[0]:
                        return station
        
        return None
    
    def get_relevant_data(self, query):
        """Determine what data to fetch based on the user query"""
        query_lower = query.lower()
        
        data = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'summary': ''
        }
        
        # Check if query is about bus
        if any(word in query_lower for word in ['bus', 'buses']):
            data['type'] = 'bus'
            data['summary'] = "Bus query detected - requires Bus API key"
            data['message'] = "Bus data requires an API key. Please set BUS_API_KEY in .env file."
            return data
        
        # Check if query is about LIRR
        if any(word in query_lower for word in ['lirr', 'long island rail', 'railroad']):
            data['type'] = 'lirr'
            station = self._extract_text_after_keywords(query, ['at', 'from', 'to', 'station'])
            data['station'] = station
            data['summary'] = "LIRR query detected"
            data['message'] = "LIRR data requires an API key. Please set LIRR_API_KEY in .env file."
            return data
        
        # Check if query is about Metro-North
        if any(word in query_lower for word in ['metro-north', 'metro north', 'metronorth']):
            data['type'] = 'metro_north'
            station = self._extract_text_after_keywords(query, ['at', 'from', 'to', 'station'])
            data['station'] = station
            data['summary'] = "Metro-North query detected"
            data['message'] = "Metro-North data requires an API key."
            return data
        
        # Check if query is about train arrivals
        if any(word in query_lower for word in ['next', 'train', 'arrive', 'when', 'time', 'coming']):
            train_line = self._extract_train_line(query)
            station_query = self._extract_station_text(query)
            station = self.find_station(station_query) if station_query else None
            
            if train_line and station:
                data['type'] = 'train_arrival'
                data['train_line'] = train_line
                data['station'] = station['stop_name']
                data['station_obj'] = station
                data['arrivals'] = self.get_train_arrivals(train_line, station)
                data['summary'] = f"Fetched arrival times for {train_line} train at {station['stop_name']}"
            else:
                data['type'] = 'train_general'
                data['summary'] = "General train query"
                if not train_line:
                    data['need_train_line'] = True
                if not station:
                    data['need_station'] = True
                    data['station_query'] = station_query
        
        # Check if query is about elevators
        elif any(word in query_lower for word in ['elevator', 'accessibility', 'accessible', 'escalator', 'ada', 'wheelchair']):
            station_query = self._extract_station_text(query)
            station = self.find_station(station_query) if station_query else None
            data['type'] = 'elevator'
            data['station'] = station['stop_name'] if station else None
            data['elevator_status'] = self.get_elevator_status(station)
            data['summary'] = f"Fetched elevator status" + (f" for {station['stop_name']}" if station else "")
        
        # Check if query is about service alerts
        elif any(word in query_lower for word in ['alert', 'delay', 'service', 'problem', 'issue', 'running']):
            train_line = self._extract_train_line(query)
            data['type'] = 'alerts'
            data['train_line'] = train_line
            data['alerts'] = self.get_service_alerts(train_line)
            data['summary'] = f"Fetched service alerts" + (f" for {train_line} line" if train_line else "")
        
        else:
            data['type'] = 'general'
            data['summary'] = "General transit query"
        
        return data
    
    def get_train_arrivals(self, train_line, station):
        """Get real-time train arrival information"""
        try:
            feed_key = self._get_feed_key(train_line)
            if not feed_key:
                return {'error': f'Unknown train line: {train_line}'}
            
            feed_url = self.FEED_URLS.get(feed_key)
            response = self.session.get(feed_url, timeout=10)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            arrivals = []
            station_ids = station.get('gtfs_stop_ids', [])
            
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    trip = entity.trip_update.trip
                    
                    # Robust route matching
                    if hasattr(trip, 'route_id') and trip.route_id:
                        trip_route = trip.route_id.strip().upper()
                        target_route = train_line.strip().upper()
                        
                        if trip_route == target_route:
                            for stop_time_update in entity.trip_update.stop_time_update:
                                # Check matches
                                if any(sid in stop_time_update.stop_id for sid in station_ids):
                                    # Use arrival time, fallback to departure time
                                    arrival_time = None
                                    if stop_time_update.HasField('arrival'):
                                        arrival_time = stop_time_update.arrival.time
                                    elif stop_time_update.HasField('departure'):
                                        arrival_time = stop_time_update.departure.time
                                    
                                    if arrival_time:
                                        arrival_datetime = datetime.fromtimestamp(arrival_time)
                                        # Calculate difference in minutes
                                        diff = (arrival_datetime - datetime.now())
                                        minutes_away = int(diff.total_seconds() / 60)
                                        
                                        # Only show future/recent trains (allow -1 min for slight delay)
                                        if minutes_away >= -1:
                                            arrivals.append({
                                                'train_line': trip_route,
                                                'direction': self._get_direction(stop_time_update.stop_id),
                                                'arrival_time': arrival_datetime.strftime('%I:%M %p'),
                                                'minutes_away': max(0, minutes_away),
                                                'stop_id': stop_time_update.stop_id
                                            })
            
            arrivals.sort(key=lambda x: x['minutes_away'])
            return arrivals[:5]
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_vehicle_positions(self, train_line=None):
        """Get live vehicle positions for trains"""
        positions = []
        try:
            # If train_line is provided, get specific feed, otherwise check all relevant feeds
            feeds_to_check = []
            if train_line:
                key = self._get_feed_key(train_line)
                if key:
                    feeds_to_check = [key]
            else:
                # Check major lines by default if no specific line req (limit to avoid too many requests if needed, but here we do all)
                feeds_to_check = list(self.FEED_URLS.keys())

            for key in feeds_to_check:
                url = self.FEED_URLS[key]
                try:
                    response = self.session.get(url, timeout=5)
                    if response.status_code != 200:
                        continue
                        
                    feed = gtfs_realtime_pb2.FeedMessage()
                    feed.ParseFromString(response.content)
                    
                    for entity in feed.entity:
                        if entity.HasField('vehicle'):
                            v = entity.vehicle
                            if not v.trip.route_id:
                                continue
                                
                            # Filter if specific line requested
                            if train_line and v.trip.route_id.upper() != train_line.upper():
                                continue

                            positions.append({
                                'id': entity.id,
                                'route_id': v.trip.route_id,
                                'lat': v.position.latitude,
                                'lon': v.position.longitude,
                                'bearing': v.position.bearing,
                                'current_status': v.current_status, # 0=INCOMING, 1=STOPPED_AT, 2=IN_TRANSIT_TO
                                'stop_id': v.stop_id,
                                'timestamp': v.timestamp
                            })
                except Exception as e:
                    print(f"Error fetching feed {key}: {e}")
                    continue
                    
            return positions

        except Exception as e:
            return {'error': str(e)}

    def get_service_alerts(self, train_line=None):
        """Get service alerts"""
        try:
            response = self.session.get(self.ALERTS_URL, timeout=10)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            alerts = []
            for entity in feed.entity:
                if entity.HasField('alert'):
                    alert = entity.alert
                    
                    if train_line:
                        route_match = False
                        for informed_entity in alert.informed_entity:
                            if hasattr(informed_entity, 'route_id') and informed_entity.route_id.upper() == train_line.upper():
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
    
    def get_elevator_status(self, station):
        """Get elevator status using dedicated elevator service"""
        from services.elevator_service import ElevatorEscalatorService
        
        # Initialize elevator service with API key
        elevator_service = ElevatorEscalatorService()
        
        if not station:
            return {'message': 'Please specify a station'}
        
        # Get equipment status for this station
        status = elevator_service.get_station_equipment_status(station['stop_name'])
        
        return status

    
    def _extract_train_line(self, query):
        """Extract train line from query"""
        patterns = [
            r'\b([ABCDEFGJLMNQRWZ])\s+(?:train|line)',
            r'(?:train|line)\s+([ABCDEFGJLMNQRWZ])\b',
            r'\b([1-7])\s+(?:train|line)',
            r'(?:train|line)\s+([1-7])\b',
            r'\b([ABCDEFGJLMNQRWZ])\b(?=\s+(?:from|at|to))',
            r'the\s+([ABCDEFGJLMNQRWZ1-7])\s+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _extract_station_text(self, query):
        """Extract station reference from query with better context awareness"""
        # Remove train line references first
        query_clean = re.sub(r'\b[ABCDEFGJLMNQRWZ1-7]\s+(?:train|line)\b', '', query, flags=re.IGNORECASE)
        query_clean = re.sub(r'(?:train|line)\s+[ABCDEFGJLMNQRWZ1-7]\b', '', query_clean, flags=re.IGNORECASE)
        
        # Common patterns for station extraction
        patterns = [
            r'(?:at|from|to|near)\s+([^?\.!]+?)(?:\s+station)?(?:\?|$|at|from|to)',
            r'(?:station)\s+([^?\.!]+?)(?:\?|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_clean, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matched, try to extract the main content after common question words
        words_to_remove = ['when', 'is', 'the', 'next', 'arriving', 'arrive', 'coming', 'train', 'line']
        words = query_clean.split()
        filtered = [w for w in words if w.lower() not in words_to_remove]
        
        if filtered:
            return ' '.join(filtered).strip()
        
        return query_clean.strip()
    
    def _extract_text_after_keywords(self, query, keywords):
        """Extract text after specific keywords"""
        for keyword in keywords:
            pattern = f'{keyword}\\s+([^?]+)'
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _get_feed_key(self, train_line):
        """Determine which feed to use for a given train line"""
        train_line = train_line.upper()
        
        feed_mapping = {
            'A': 'ace', 'C': 'ace', 'E': 'ace',
            'B': 'bdfm', 'D': 'bdfm', 'F': 'bdfm', 'M': 'bdfm',
            'G': 'g',
            'J': 'jz', 'Z': 'jz',
            'N': 'nqrw', 'Q': 'nqrw', 'R': 'nqrw', 'W': 'nqrw',
            'L': 'l',
            '1': '1234567', '2': '1234567', '3': '1234567',
            '4': '1234567', '5': '1234567', '6': '1234567', '7': '1234567'
        }
        
        return feed_mapping.get(train_line)
    
    def _get_direction(self, stop_id):
        """Determine direction from stop ID"""
        if stop_id.endswith('N'):
            return 'Uptown/Bronx/Queens'
        elif stop_id.endswith('S'):
            return 'Downtown/Brooklyn'
        return 'Unknown'
