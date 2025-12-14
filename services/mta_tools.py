from langchain_core.tools import tool
from typing import Optional, List, Dict
import logging
from services.lirr_service import LIRRService
from services.mta_service import MTAService
from services.elevator_service import ElevatorEscalatorService
import os

logger = logging.getLogger(__name__)

# Initialize services
mta_service = MTAService()
elevator_service = ElevatorEscalatorService()


@tool
def get_train_arrivals(train_line: str, station_name: str) -> str:
    """
    Get real-time train arrival times for a specific train line at a station.
    
    Args:
        train_line: The train line (e.g., 'N', 'Q', '1', '2', 'A', etc.)
        station_name: The station name (e.g., 'Times Square', '59th St', 'Penn Station')
    
    Returns:
        String with upcoming train arrival times
    """
    logger.info(f"Tool called: get_train_arrivals({train_line}, {station_name})")
    
    # Find the station
    station = mta_service.find_station(station_name)
    
    if not station:
        return f"Could not find station: {station_name}. Please try a different station name."
    
    # Get arrivals
    arrivals = mta_service.get_train_arrivals(train_line.upper(), station)
    
    if isinstance(arrivals, dict) and 'error' in arrivals:
        return f"Error fetching arrivals: {arrivals['error']}"
    
    if not arrivals:
        return f"No upcoming {train_line} trains found at {station['stop_name']} in the next 30 minutes."
    
    # Format response
    result = f"Upcoming {train_line} trains at {station['stop_name']}:\n"
    for i, arrival in enumerate(arrivals, 1):
        result += f"{i}. {arrival['direction']} - {arrival['arrival_time']} ({arrival['minutes_away']} min)\n"
    
    return result


@tool
def get_service_alerts(train_line: Optional[str] = None) -> str:
    """
    Get service alerts and delays for NYC subway.
    
    Args:
        train_line: Optional specific train line (e.g., 'N', 'Q', '1'). If None, returns all alerts.
    
    Returns:
        String with current service alerts
    """
    logger.info(f"Tool called: get_service_alerts({train_line})")
    
    alerts = mta_service.get_service_alerts(train_line.upper() if train_line else None)
    
    if isinstance(alerts, dict) and 'error' in alerts:
        return f"Error fetching alerts: {alerts['error']}"
    
    if not alerts:
        line_text = f"the {train_line} line" if train_line else "any train lines"
        return f"✓ Good news! No service alerts for {line_text}. Trains are running normally."
    
    # Format alerts
    result = f"Service Alerts" + (f" for {train_line} line" if train_line else "") + ":\n\n"
    for i, alert in enumerate(alerts[:5], 1):
        result += f"{i}. {alert['header']}\n"
        if alert['affected_routes']:
            result += f"   Affects: {', '.join(alert['affected_routes'])}\n"
        result += "\n"
    
    return result


@tool
def get_elevator_status(station_name: str) -> str:
    """
    Get elevator and escalator status at a specific station.
    
    Args:
        station_name: The station name (e.g., 'Times Square', 'Penn Station', '42nd St')
    
    Returns:
        String with elevator/escalator status
    """
    logger.info(f"Tool called: get_elevator_status({station_name})")
    
    status = elevator_service.get_station_equipment_status(station_name)
    
    if 'error' in status:
        return f"Error checking elevator status: {status['error']}"
    
    if 'message' in status:
        # Station not found or no equipment
        return f"{status['message']}\n\nNote: {status.get('suggestion', 'Some stations do not have elevators or escalators.')}"
    
    # Format status
    result = f"Elevator/Escalator Status at {status['station']}:\n"
    result += f"Total Equipment: {status['total_equipment']}\n"
    result += f"✅ Operational: {status['operational']}\n"
    result += f"❌ Out of Service: {status['out_of_service']}\n"
    
    if status['out_of_service'] == 0:
        result += "\n✓ All elevators and escalators are operational!"
    else:
        result += "\nDetails:\n"
        for equip in status['equipment']:
            if equip['is_out_of_service']:
                equip_type = "Elevator" if equip['equipment_type'] == 'EL' else "Escalator"
                result += f"  ❌ {equip_type} - {equip['serving']} (OUT OF SERVICE)\n"
    
    return result



@tool
def find_nearby_stations(station_name: str) -> str:
    """
    Find stations with similar names or nearby the specified station.
    Useful when user provides incomplete or ambiguous station names.
    
    Args:
        station_name: Partial or complete station name
    
    Returns:
        String with list of matching stations
    """
    logger.info(f"Tool called: find_nearby_stations({station_name})")
    
    from rapidfuzz import fuzz, process
    
    station_names = [s['stop_name'] for s in mta_service.stations]
    
    # Get top 5 matches
    matches = process.extract(
        station_name,
        station_names,
        scorer=fuzz.token_sort_ratio,
        limit=5
    )
    
    if not matches:
        return f"No stations found matching '{station_name}'"
    
    result = f"Stations matching '{station_name}':\n"
    for i, (name, score, _) in enumerate(matches, 1):
        # Find station details
        station = next((s for s in mta_service.stations if s['stop_name'] == name), None)
        if station:
            routes = ', '.join(station['routes'][:5])
            result += f"{i}. {name} ({routes}) - {station['borough']}\n"
    
    return result
@tool
def plan_trip(from_station: str, to_station: str) -> str:
    """
    Plan a trip between two stations. Shows which trains to take and transfer points.
    
    Args:
        from_station: Starting station name (e.g., 'Jay St MetroTech', 'Times Square')
        to_station: Destination station name (e.g., '8th St NYU', 'Penn Station')
    
    Returns:
        String with trip plan including trains to take and transfers
    """
    logger.info(f"Tool called: plan_trip({from_station}, {to_station})")
    
    # Find both stations
    origin = mta_service.find_station(from_station)
    destination = mta_service.find_station(to_station)
    
    if not origin:
        return f"Could not find origin station: {from_station}. Please check the station name."
    
    if not destination:
        return f"Could not find destination station: {to_station}. Please check the station name."
    
    # Get routes at each station
    origin_routes = set(origin['routes'])
    dest_routes = set(destination['routes'])
    
    # Find direct routes (no transfer needed)
    direct_routes = origin_routes.intersection(dest_routes)
    
    result = f"Trip from {origin['stop_name']} to {destination['stop_name']}:\n\n"
    
    if direct_routes:
        result += "✅ DIRECT ROUTE (No transfer needed):\n"
        for route in sorted(direct_routes):
            result += f"  • Take the {route} train from {origin['stop_name']} to {destination['stop_name']}\n"
        
        # Get current train times for direct routes
        result += "\n📍 Current arrivals:\n"
        for route in sorted(direct_routes):
            arrivals = mta_service.get_train_arrivals(route, origin)
            if arrivals and not isinstance(arrivals, dict):
                next_train = arrivals[0] if arrivals else None
                if next_train:
                    result += f"  • {route} train: {next_train['minutes_away']} min ({next_train['arrival_time']})\n"
    else:
        result += "🔄 TRANSFER REQUIRED:\n"
        result += f"Origin trains: {', '.join(sorted(origin_routes))}\n"
        result += f"Destination trains: {', '.join(sorted(dest_routes))}\n\n"
        
        # Find common transfer stations
        transfer_suggestions = find_transfer_stations(origin_routes, dest_routes)
        
        if transfer_suggestions:
            result += "Suggested routes:\n"
            for i, suggestion in enumerate(transfer_suggestions[:3], 1):
                result += f"\n{i}. Take {suggestion['from_route']} from {origin['stop_name']}\n"
                result += f"   Transfer at {suggestion['transfer_station']} to {suggestion['to_route']}\n"
                result += f"   Continue to {destination['stop_name']}\n"
        else:
            result += "\nRecommended approach:\n"
            result += f"1. From {origin['stop_name']}, take any of: {', '.join(sorted(origin_routes))}\n"
            result += f"2. Transfer to a train that serves {destination['stop_name']}: {', '.join(sorted(dest_routes))}\n"
            result += "\nCommon transfer points: Times Square, Union Square, Atlantic Ave, or Fulton St\n"
    
    return result


def find_transfer_stations(origin_routes: set, dest_routes: set) -> list:
    """
    Find stations where you can transfer between route sets
    
    Args:
        origin_routes: Set of routes at origin
        dest_routes: Set of routes at destination
    
    Returns:
        List of transfer suggestions
    """
    # Major transfer hubs with their routes
    transfer_hubs = {
        'Times Sq-42 St': ['1', '2', '3', '7', 'N', 'Q', 'R', 'W', 'S'],
        '14 St-Union Sq': ['4', '5', '6', 'L', 'N', 'Q', 'R', 'W'],
        'Atlantic Ave-Barclays Ctr': ['2', '3', '4', '5', 'B', 'D', 'N', 'Q', 'R'],
        'Fulton St': ['2', '3', '4', '5', 'A', 'C', 'J', 'Z'],
        '59 St-Columbus Circle': ['1', 'A', 'B', 'C', 'D'],
        'Jay St-MetroTech': ['A', 'C', 'F', 'R'],
        'Lexington Ave/59 St': ['4', '5', '6', 'N', 'Q', 'R', 'W'],
        'Herald Sq': ['B', 'D', 'F', 'M', 'N', 'Q', 'R', 'W'],
    }
    
    suggestions = []
    
    for station, routes in transfer_hubs.items():
        station_routes = set(routes)
        
        # Check if this hub connects origin and destination routes
        origin_match = origin_routes.intersection(station_routes)
        dest_match = dest_routes.intersection(station_routes)
        
        if origin_match and dest_match:
            for from_route in origin_match:
                for to_route in dest_match:
                    if from_route != to_route:
                        suggestions.append({
                            'transfer_station': station,
                            'from_route': from_route,
                            'to_route': to_route
                        })
    
    return suggestions

# Import LIRR tool functions directly
from services.lirr_service import LIRRService

lirr_service = LIRRService()

@tool
def get_lirr_train_arrivals_func(station_name: str) -> str:
    """Get LIRR train arrivals"""
    try:
        logger.info(f"LIRR Tool called: get_lirr_train_arrivals({station_name})")
        
        arrivals = lirr_service.get_train_arrivals(station_name)
        
        if isinstance(arrivals, dict) and 'error' in arrivals:
            return f"Error: {arrivals['error']}"
        
        if not arrivals:
            return f"No upcoming LIRR trains found at {station_name}"
        
        station = lirr_service.find_station(station_name)
        station_display = station['name'] if station else station_name
        
        result = f"Upcoming LIRR trains at {station_display}:\n\n"
        for i, arrival in enumerate(arrivals, 1):
            track_info = f"Track {arrival['track']}" if arrival['track'] != 'TBD' else "Track TBD"
            result += f"{i}. To {arrival['destination']} - {arrival['arrival_time']} ({arrival['minutes_away']} min) - {track_info}\n"
        
        return result
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_lirr_service_alerts_func(input_str: str = "") -> str:
    """Get LIRR service alerts"""
    try:
        logger.info("LIRR Tool called: get_lirr_service_alerts()")
        
        alerts = lirr_service.get_service_alerts()
        
        if isinstance(alerts, dict) and 'error' in alerts:
            return f"Error: {alerts['error']}"
        
        if not alerts:
            return "✓ No LIRR service alerts. Trains running on schedule!"
        
        result = f"LIRR Service Alerts ({len(alerts)} active):\n\n"
        for i, alert in enumerate(alerts[:5], 1):
            result += f"{i}. {alert['header']}\n"
            if alert['affected_lines']:
                result += f"   Affected: {', '.join(alert['affected_lines'])}\n"
            result += "\n"
        
        return result
    except Exception as e:
        return f"Error: {str(e)}"





# Update the mta_tools list at the bottom
mta_tools = [
    get_train_arrivals,
    get_service_alerts,
    get_elevator_status,
    find_nearby_stations,
    plan_trip,  # NEW: Add trip planning tool
    get_lirr_train_arrivals_func,
    get_lirr_service_alerts_func
]

