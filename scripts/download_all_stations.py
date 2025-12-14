import json
import requests
import csv
from io import StringIO
from collections import defaultdict

def download_complete_stations():
    """
    Download all NYC subway stations from official NYC Open Data
    Source: https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f
    """
    
    print("📥 Downloading complete NYC subway station data...")
    
    # NYC Open Data API endpoint for subway stations
    url = "https://data.ny.gov/resource/39hk-dx4f.json"
    
    # Add limit parameter to get all records
    params = {
        '$limit': 10000,  # Get all stations
        '$order': 'stop_name'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Downloaded {len(data)} station records")
        
        # Process and deduplicate stations
        stations_dict = {}
        
        for record in data:
            stop_id = record.get('gtfs_stop_id', '').strip()
            stop_name = record.get('stop_name', '').strip()
            
            if not stop_id or not stop_name:
                continue
            
            # Get coordinates
            try:
                lat = float(record.get('gtfs_latitude', 0))
                lon = float(record.get('gtfs_longitude', 0))
            except (ValueError, TypeError):
                lat, lon = 0.0, 0.0
            
            # Parse routes (space-separated in the data)
            daytime_routes = record.get('daytime_routes', '').strip()
            routes = [r.strip() for r in daytime_routes.split() if r.strip()]
            
            # Get borough
            borough = record.get('borough', '').strip()
            
            # Use complex_id to group related platforms
            complex_id = record.get('complex_id', stop_id)
            
            if complex_id not in stations_dict:
                # Generate GTFS stop IDs with directional suffixes
                base_id = stop_id.rstrip('NS')  # Remove existing N/S
                gtfs_ids = [base_id]
                if not base_id.endswith('N') and not base_id.endswith('S'):
                    gtfs_ids.extend([f"{base_id}N", f"{base_id}S"])
                
                stations_dict[complex_id] = {
                    'stop_id': base_id,
                    'stop_name': stop_name,
                    'stop_lat': lat,
                    'stop_lon': lon,
                    'routes': routes,
                    'borough': borough,
                    'gtfs_stop_ids': gtfs_ids
                }
            else:
                # Merge routes for same complex
                existing = stations_dict[complex_id]
                existing['routes'] = list(set(existing['routes'] + routes))
        
        # Convert to list and sort
        stations_list = list(stations_dict.values())
        stations_list.sort(key=lambda x: x['stop_name'])
        
        print(f"✓ Processed {len(stations_list)} unique stations")
        
        # Create output data
        output_data = {
            'stations': stations_list,
            'metadata': {
                'total_stations': len(stations_list),
                'last_updated': '2025-11-06',
                'source': 'NYC Open Data - MTA Subway Stations',
                'source_url': 'https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f'
            }
        }
        
        # Save to file
        import os
        os.makedirs('data', exist_ok=True)
        
        output_file = 'data/subway_stations.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved to {output_file}")
        
        # Print statistics
        print("\n📊 Statistics:")
        print(f"   Total stations: {len(stations_list)}")
        
        # Count by borough
        borough_counts = defaultdict(int)
        for station in stations_list:
            borough_counts[station['borough']] += 1
        
        print("\n   Stations by borough:")
        for borough, count in sorted(borough_counts.items()):
            print(f"   - {borough}: {count}")
        
        # Count routes
        all_routes = set()
        for station in stations_list:
            all_routes.update(station['routes'])
        
        print(f"\n   Total routes: {len(all_routes)}")
        print(f"   Routes: {', '.join(sorted(all_routes))}")
        
        # Show sample stations
        print("\n📍 Sample stations:")
        for station in stations_list[:10]:
            routes_str = ', '.join(sorted(station['routes']))
            print(f"   - {station['stop_name']} ({routes_str})")
        
        # Check for Jay St-MetroTech specifically
        jay_st = next((s for s in stations_list if 'jay st' in s['stop_name'].lower()), None)
        if jay_st:
            print(f"\n✓ Found Jay St-MetroTech: {jay_st['stop_name']}")
            print(f"  Routes: {', '.join(jay_st['routes'])}")
        
        print("\n✅ Success! All stations downloaded.")
        return True
        
    except requests.RequestException as e:
        print(f"✗ Error downloading data: {e}")
        return False
    except Exception as e:
        print(f"✗ Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    download_complete_stations()
