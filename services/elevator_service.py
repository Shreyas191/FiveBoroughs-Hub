import requests
import json
from datetime import datetime
import time
import logging
from rapidfuzz import fuzz, process
from config.logging_config import api_logger

logger = logging.getLogger(__name__)

class ElevatorEscalatorService:
    """Service for MTA Elevator & Escalator Equipment Status"""
    
    EQUIPMENT_URL = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fnyct_ene_equipments.json'
    OUTAGE_URL = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fnyct_ene.json'
    
    def __init__(self):
        self.session = requests.Session()
        self.equipment_cache = None
        self.cache_timestamp = None
    
    def _normalize_station_name(self, name):
        """
        Normalize station name for better matching
        Handles variations like:
        - "Times Sq-42 St" vs "Times Square - 42nd Street"
        - "Penn Station" vs "34 St - Penn Station"
        """
        if not name:
            return ""
        
        normalized = name.lower()
        
        # Common replacements
        replacements = {
            'street': 'st',
            'avenue': 'ave',
            'square': 'sq',
            'saint': 'st',
            'first': '1st',
            'second': '2nd',
            'third': '3rd',
            'fourth': '4th',
            'fifth': '5th',
            'sixth': '6th',
            'seventh': '7th',
            'eighth': '8th',
            'ninth': '9th',
            'penn station': 'penn',
            'grand central': 'grd cntrl',
            'port authority': 'port auth'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra punctuation and spaces
        normalized = normalized.replace('-', ' ').replace('/', ' ')
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _find_station_in_equipment(self, station_name, equipment_list):
        """
        Find station in equipment list using fuzzy matching
        
        Args:
            station_name: Station name to search for
            equipment_list: List of all equipment
        
        Returns:
            List of equipment at the matching station
        """
        # Get all unique station names from equipment
        station_names_in_equipment = list(set(
            eq.get('station', '') for eq in equipment_list if eq.get('station')
        ))
        
        # Normalize search query
        normalized_query = self._normalize_station_name(station_name)
        
        # Try exact match first
        matches = []
        for eq_station in station_names_in_equipment:
            if self._normalize_station_name(eq_station) == normalized_query:
                matches = [eq for eq in equipment_list if eq.get('station') == eq_station]
                logger.info(f"Exact match found: {eq_station}")
                return matches
        
        # Try fuzzy matching
        logger.info(f"No exact match, trying fuzzy matching for: {station_name}")
        
        # Use rapidfuzz to find best matches
        best_matches = process.extract(
            normalized_query,
            [self._normalize_station_name(s) for s in station_names_in_equipment],
            scorer=fuzz.token_sort_ratio,
            limit=3
        )
        
        logger.info(f"Fuzzy matches: {best_matches}")
        
        # If we have a good match (>70% similarity)
        if best_matches and best_matches[0][1] > 70:
            # Get the original station name
            matched_normalized = best_matches[0][0]
            matched_station = next(
                (s for s in station_names_in_equipment 
                 if self._normalize_station_name(s) == matched_normalized),
                None
            )
            
            if matched_station:
                logger.info(f"Using fuzzy match: {matched_station} (score: {best_matches[0][1]})")
                matches = [eq for eq in equipment_list if eq.get('station') == matched_station]
                return matches
        
        return []
    
    def get_station_equipment_status(self, station_name):
        """
        Get elevator/escalator status for a specific station with improved matching
        """
        # Get all equipment
        equipment_data = self.get_all_equipment()
        if 'error' in equipment_data:
            return equipment_data
        
        # Get current outages
        outage_data = self.get_outages()
        if 'error' in outage_data:
            outage_data = []
        
        # Extract equipment list
        equipment_list = equipment_data
        if isinstance(equipment_data, dict):
            equipment_list = equipment_data.get('equipment', [])
        
        # Extract outage IDs
        outage_ids = set()
        if isinstance(outage_data, list):
            outage_ids = {item.get('equipment') for item in outage_data if item.get('equipment')}
        elif isinstance(outage_data, dict) and 'outages' in outage_data:
            outage_ids = {item.get('equipment') for item in outage_data.get('outages', []) if item.get('equipment')}
        
        # Find equipment at this station using fuzzy matching
        station_equipment_raw = self._find_station_in_equipment(station_name, equipment_list)
        
        if not station_equipment_raw:
            # Try alternate names
            alternate_names = self._get_alternate_station_names(station_name)
            for alt_name in alternate_names:
                logger.info(f"Trying alternate name: {alt_name}")
                station_equipment_raw = self._find_station_in_equipment(alt_name, equipment_list)
                if station_equipment_raw:
                    break
        
        if not station_equipment_raw:
            # Return helpful message with suggestions
            return {
                'station': station_name,
                'message': f'No elevators or escalators found at "{station_name}"',
                'suggestion': 'This station may not have elevators/escalators, or try a different station name variation.',
                'equipment': []
            }
        
        # Process equipment
        station_equipment = []
        actual_station_name = station_equipment_raw[0].get('station', station_name) if station_equipment_raw else station_name
        
        for equipment in station_equipment_raw:
            equipment_id = equipment.get('equipmentno')
            is_out = equipment_id in outage_ids
            
            station_equipment.append({
                'equipment_id': equipment_id,
                'equipment_type': equipment.get('equipmenttype', 'Unknown'),
                'serving': equipment.get('serving', 'Unknown'),
                'ada': equipment.get('ada', False),
                'station': equipment.get('station', 'Unknown'),
                'borough': equipment.get('borough', 'Unknown'),
                'is_out_of_service': is_out,
                'status': 'Out of Service' if is_out else 'Operational'
            })
        
        return {
            'station': actual_station_name,
            'equipment': station_equipment,
            'total_equipment': len(station_equipment),
            'operational': len([e for e in station_equipment if not e['is_out_of_service']]),
            'out_of_service': len([e for e in station_equipment if e['is_out_of_service']])
        }
    
    def _get_alternate_station_names(self, station_name):
        """
        Generate alternate names for a station
        
        Examples:
        - "Times Sq-42 St" → ["Times Square", "42nd Street", "Times Square 42", "42 St"]
        - "Penn Station" → ["34 St Penn Station", "Pennsylvania Station"]
        """
        alternates = []
        name_lower = station_name.lower()
        
        # Common variations
        if 'times sq' in name_lower or 'times square' in name_lower:
            alternates.extend(['Times Square', '42nd Street', 'Times Sq 42', '42 St Times Sq'])
        
        if 'penn' in name_lower:
            alternates.extend(['34 St Penn Station', 'Pennsylvania Station', '34 St'])
        
        if 'grand central' in name_lower:
            alternates.extend(['Grand Central 42 St', '42 St Grand Central', 'Grand Central Terminal'])
        
        if 'world trade' in name_lower or 'wtc' in name_lower:
            alternates.extend(['World Trade Center', 'WTC Cortlandt', 'Cortlandt St'])
        
        if 'jay st' in name_lower:
            alternates.extend(['Jay Street MetroTech', 'Jay St MetroTech', 'Jay Street'])
        
        if 'atlantic' in name_lower:
            alternates.extend(['Atlantic Av Barclays Ctr', 'Atlantic Avenue', 'Barclays Center'])
        
        if 'herald sq' in name_lower or 'herald square' in name_lower:
            alternates.extend(['34 St Herald Sq', 'Herald Square', '34 St Herald Square'])
        
        if 'union sq' in name_lower or 'union square' in name_lower:
            alternates.extend(['14 St Union Sq', 'Union Square', '14 St Union Square'])
        
        # Add version with "St" expanded to "Street"
        if ' st' in name_lower and 'street' not in name_lower:
            alternates.append(station_name.replace(' St', ' Street'))
        
        # Add version with "Ave" expanded to "Avenue"
        if ' ave' in name_lower and 'avenue' not in name_lower:
            alternates.append(station_name.replace(' Ave', ' Avenue'))
        
        return alternates
    
    # Keep all other methods the same (get_all_equipment, get_outages, etc.)
    
    def get_all_equipment(self, force_refresh=False):
        """Get list of all elevators and escalators with logging"""
        # Check cache first
        if not force_refresh and self.equipment_cache and self.cache_timestamp:
            if (datetime.now() - self.cache_timestamp).seconds < 300:
                logger.debug("Returning cached equipment data")
                return self.equipment_cache
        
        start_time = time.time()
        
        try:
            logger.info("Fetching all elevator/escalator equipment data")
            
            response = self.session.get(self.EQUIPMENT_URL, timeout=10)
            response_time = time.time() - start_time
            
            api_logger.log_api_call(
                service_name='MTA_ELEVATOR_EQUIPMENT',
                endpoint=self.EQUIPMENT_URL,
                method='GET',
                headers=dict(self.session.headers),
                response_status=response.status_code,
                response_time=response_time
            )
            
            response.raise_for_status()
            data = response.json()
            
            self.equipment_cache = data
            self.cache_timestamp = datetime.now()
            
            equipment_count = len(data) if isinstance(data, list) else len(data.get('equipment', []))
            logger.info(f"Successfully fetched {equipment_count} pieces of equipment")
            
            return data
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f'Failed to fetch equipment data: {str(e)}'
            logger.error(error_msg)
            
            api_logger.log_api_call(
                service_name='MTA_ELEVATOR_EQUIPMENT',
                endpoint=self.EQUIPMENT_URL,
                method='GET',
                response_time=response_time,
                error=error_msg
            )
            
            return {'error': error_msg}
    
    def get_outages(self):
        """Get current elevator and escalator outages with logging"""
        start_time = time.time()
        
        try:
            logger.info("Fetching elevator/escalator outages")
            
            response = self.session.get(self.OUTAGE_URL, timeout=10)
            response_time = time.time() - start_time
            
            data = response.json()
            outage_count = len(data) if isinstance(data, list) else len(data.get('outages', []))
            
            api_logger.log_api_call(
                service_name='MTA_ELEVATOR_OUTAGES',
                endpoint=self.OUTAGE_URL,
                method='GET',
                headers=dict(self.session.headers),
                response_status=response.status_code,
                response_time=response_time,
                response_data={'outage_count': outage_count}
            )
            
            logger.info(f"Found {outage_count} current outages")
            return data
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f'Failed to fetch outage data: {str(e)}'
            logger.error(error_msg)
            
            api_logger.log_api_call(
                service_name='MTA_ELEVATOR_OUTAGES',
                endpoint=self.OUTAGE_URL,
                method='GET',
                response_time=response_time,
                error=error_msg
            )
            
            return {'error': error_msg}
