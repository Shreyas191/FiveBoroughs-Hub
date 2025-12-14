from langchain.agents import Tool
from services.lirr_service import LIRRService
import os
import logging

logger = logging.getLogger(__name__)

# Initialize LIRR service
lirr_service = LIRRService(api_key=os.getenv('LIRR_API_KEY'))


def get_lirr_train_arrivals_func(station_name: str) -> str:
    """
    Get LIRR train arrival times at a station
    
    Args:
        station_name: LIRR station name (e.g., 'Penn Station', 'Jamaica', 'Hicksville')
    
    Returns:
        String with upcoming LIRR train times
    """
    try:
        logger.info(f"LIRR Tool called: get_lirr_train_arrivals({station_name})")
        
        arrivals = lirr_service.get_train_arrivals(station_name)
        
        if isinstance(arrivals, dict) and 'error' in arrivals:
            return f"Error: {arrivals['error']}"
        
        if not arrivals:
            return f"No upcoming LIRR trains found at {station_name} in the next hour."
        
        # Format response
        station = lirr_service.find_station(station_name)
        station_display = station['name'] if station else station_name
        
        result = f"Upcoming LIRR trains at {station_display}:\n\n"
        for i, arrival in enumerate(arrivals, 1):
            track_info = f"Track {arrival['track']}" if arrival['track'] != 'TBD' else "Track TBD"
            result += f"{i}. To {arrival['destination']} - {arrival['arrival_time']} ({arrival['minutes_away']} min) - {track_info}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_lirr_train_arrivals: {str(e)}", exc_info=True)
        return f"Error getting LIRR train times: {str(e)}"


def get_lirr_service_alerts_func(input_str: str = "") -> str:
    """
    Get LIRR service alerts and delays
    
    Returns:
        String with current LIRR service alerts
    """
    try:
        logger.info("LIRR Tool called: get_lirr_service_alerts()")
        
        alerts = lirr_service.get_service_alerts()
        
        if isinstance(alerts, dict) and 'error' in alerts:
            return f"Error: {alerts['error']}"
        
        if not alerts:
            return "✓ No LIRR service alerts at this time. Trains are running on schedule!"
        
        # Format response
        result = f"LIRR Service Alerts ({len(alerts)} active):\n\n"
        
        for i, alert in enumerate(alerts[:5], 1):  # Show first 5
            result += f"{i}. {alert['header']}\n"
            if alert['affected_lines']:
                result += f"   Affected: {', '.join(alert['affected_lines'])}\n"
            if alert['description']:
                # Truncate long descriptions
                desc = alert['description'][:200]
                if len(alert['description']) > 200:
                    desc += "..."
                result += f"   Details: {desc}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_lirr_service_alerts: {str(e)}", exc_info=True)
        return f"Error getting LIRR alerts: {str(e)}"


def find_lirr_station_func(query: str) -> str:
    """
    Find LIRR stations by name
    
    Args:
        query: Partial station name to search for
    
    Returns:
        String with matching LIRR stations
    """
    try:
        logger.info(f"LIRR Tool called: find_lirr_station({query})")
        
        station = lirr_service.find_station(query)
        
        if not station:
            # Show available stations
            result = f"Could not find LIRR station matching '{query}'.\n\n"
            result += "Major LIRR stations:\n"
            for name in sorted(lirr_service.lirr_stations.keys())[:10]:
                result += f"  - {name}\n"
            return result
        
        result = f"Found LIRR station: {station['name']}\n"
        result += f"Serves lines: {', '.join(station['lines'])}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in find_lirr_station: {str(e)}", exc_info=True)
        return f"Error finding station: {str(e)}"


# Define LIRR tools
lirr_tools = [
    Tool(
        name="get_lirr_train_arrivals",
        func=get_lirr_train_arrivals_func,
        description="Get LIRR (Long Island Rail Road) train arrival times at a station. Input: station name (e.g., 'Penn Station', 'Jamaica', 'Hicksville')"
    ),
    Tool(
        name="get_lirr_service_alerts",
        func=get_lirr_service_alerts_func,
        description="Get LIRR service alerts and delays. Use this when users ask about LIRR problems, delays, or service changes. No input needed."
    ),
    Tool(
        name="find_lirr_station",
        func=find_lirr_station_func,
        description="Find LIRR stations by name. Use when user mentions a location but you're not sure which LIRR station. Input: station name or area"
    ),
]
