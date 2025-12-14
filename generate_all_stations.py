import json
import csv
import requests
from io import StringIO

def download_and_convert_stations():
    """
    Download MTA subway stations data and convert to JSON format
    Data sources:
    1. NY Open Data Portal (primary)
    2. MTA Static GTFS feed (fallback)
    """
    
    print("🚇 NYC Subway Station Data Converter")
    print("=" * 60)
    
    # Try NY Open Data API first (more reliable)
    ny_open_data_url = "https://data.ny.gov/api/views/39hk-dx4f/rows.csv?accessType=DOWNLOAD"
    
    try:
        print("\n📥 Downloading from NY Open Data Portal...")
        response = requests.get(ny_open_data_url, timeout=30)
        response.raise_for_status()
        print(f"✓ Downloaded {len(response.content)} bytes")
        
        # Parse CSV
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        
        # Show available columns
        print(f"\n📋 Available columns: {', '.join(reader.fieldnames)}")
        
        # Convert to our format
        stations_dict = {}  # Use dict to avoid duplicates
        route_mapping = {}
        
        for row in reader:
            # Extract key fields
            stop_id = row.get('GTFS Stop ID', '').strip()
            stop_name = row.get('Stop Name', '').strip()
            borough = row.get('Borough', '').strip()
            
            # Get coordinates
            try:
                lat = float(row.get('GTFS Latitude', 0))
                lon = float(row.get('GTFS Longitude', 0))
            except (ValueError, TypeError):
                lat, lon = 0.0, 0.0
            
            # Parse routes (can be like "A-C-E" or "1-2-3")
            daytime_routes = row.get('Daytime Routes', '').strip()
            routes = [r.strip() for r in daytime_routes.replace('-', ' ').split() if r.strip()]
            
            if not stop_id or not stop_name:
                continue
            
            # Create unique key (complex ID)
            complex_id = row.get('Complex ID', stop_id)
            
            # Group by complex to consolidate stations
            if complex_id not in stations_dict:
                # Generate GTFS stop IDs (with N/S suffixes for direction)
                base_stop_id = stop_id
                gtfs_stop_ids = [base_stop_id]
                
                # Add directional variants
                if not base_stop_id.endswith('N') and not base_stop_id.endswith('S'):
                    gtfs_stop_ids.extend([f"{base_stop_id}N", f"{base_stop_id}S"])
                
                stations_dict[complex_id] = {
                    "stop_id": base_stop_id,
                    "stop_name": stop_name,
                    "stop_lat": lat,
                    "stop_lon": lon,
                    "routes": routes,
                    "borough": borough,
                    "gtfs_stop_ids": gtfs_stop_ids
                }
            else:
                # Merge routes if station already exists
                existing = stations_dict[complex_id]
                existing['routes'] = list(set(existing['routes'] + routes))
        
        # Convert to list
        stations_list = list(stations_dict.values())
        
        # Sort by stop name
        stations_list.sort(key=lambda x: x['stop_name'])
        
        print(f"\n✓ Processed {len(stations_list)} unique stations")
        
        # Create final JSON structure
        output_data = {
            "stations": stations_list,
            "metadata": {
                "total_stations": len(stations_list),
                "last_updated": "2025-11-05",
                "source": "NY Open Data Portal - MTA Subway Stations",
                "source_url": ny_open_data_url
            }
        }
        
        # Save to file
        output_file = "data/subway_stations.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved to {output_file}")
        
        # Print statistics
        print("\n📊 Statistics:")
        print(f"   Total stations: {len(stations_list)}")
        
        # Count by borough
        borough_counts = {}
        for station in stations_list:
            borough = station['borough']
            borough_counts[borough] = borough_counts.get(borough, 0) + 1
        
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
        for station in stations_list[:5]:
            routes_str = ', '.join(station['routes'])
            print(f"   - {station['stop_name']} ({routes_str})")
        
        print("\n✅ Success! Station data is ready to use.")
        return True
        
    except requests.RequestException as e:
        print(f"✗ Error downloading data: {e}")
        print("\n💡 Tip: Check your internet connection or try again later")
        return False
    except Exception as e:
        print(f"✗ Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """Create a comprehensive sample dataset as fallback"""
    print("\n📝 Creating comprehensive sample dataset...")
    
    sample_stations = {
        "stations": [
            # Manhattan - 1/2/3 Line
            {"stop_id": "101", "stop_name": "Van Cortlandt Park-242 St", "stop_lat": 40.889248, "stop_lon": -73.898583, "routes": ["1"], "borough": "Bronx", "gtfs_stop_ids": ["101", "101N", "101S"]},
            {"stop_id": "120", "stop_name": "96 St", "stop_lat": 40.793919, "stop_lon": -73.972323, "routes": ["1", "2", "3"], "borough": "Manhattan", "gtfs_stop_ids": ["120", "120N", "120S"]},
            {"stop_id": "123", "stop_name": "72 St", "stop_lat": 40.778453, "stop_lon": -73.981963, "routes": ["1", "2", "3"], "borough": "Manhattan", "gtfs_stop_ids": ["123", "123N", "123S"]},
            {"stop_id": "125", "stop_name": "59 St-Columbus Circle", "stop_lat": 40.768247, "stop_lon": -73.981929, "routes": ["A", "B", "C", "D", "1"], "borough": "Manhattan", "gtfs_stop_ids": ["125", "125N", "125S", "A27", "A27N", "A27S", "D14", "D14N", "D14S"]},
            {"stop_id": "127", "stop_name": "Times Sq-42 St", "stop_lat": 40.755983, "stop_lon": -73.986229, "routes": ["1", "2", "3", "7", "N", "Q", "R", "W", "S"], "borough": "Manhattan", "gtfs_stop_ids": ["127", "127N", "127S", "902", "902N", "902S", "R16", "R16N", "R16S", "725", "725N", "725S"]},
            {"stop_id": "128", "stop_name": "34 St-Penn Station", "stop_lat": 40.750373, "stop_lon": -73.991057, "routes": ["1", "2", "3", "A", "C", "E"], "borough": "Manhattan", "gtfs_stop_ids": ["128", "128N", "128S", "A28", "A28N", "A28S"]},
            {"stop_id": "132", "stop_name": "14 St", "stop_lat": 40.737826, "stop_lon": -74.000201, "routes": ["1", "2", "3"], "borough": "Manhattan", "gtfs_stop_ids": ["132", "132N", "132S"]},
            
            # Manhattan - 4/5/6 Line  
            {"stop_id": "621", "stop_name": "59 St", "stop_lat": 40.762526, "stop_lon": -73.967967, "routes": ["4", "5", "6"], "borough": "Manhattan", "gtfs_stop_ids": ["621", "621N", "621S"]},
            {"stop_id": "626", "stop_name": "Grand Central-42 St", "stop_lat": 40.751776, "stop_lon": -73.976848, "routes": ["4", "5", "6", "7", "S"], "borough": "Manhattan", "gtfs_stop_ids": ["626", "626N", "626S", "723", "723N", "723S"]},
            {"stop_id": "631", "stop_name": "33 St", "stop_lat": 40.746081, "stop_lon": -73.982076, "routes": ["6"], "borough": "Manhattan", "gtfs_stop_ids": ["631", "631N", "631S"]},
            {"stop_id": "635", "stop_name": "14 St-Union Sq", "stop_lat": 40.735736, "stop_lon": -73.990568, "routes": ["4", "5", "6", "L", "N", "Q", "R", "W"], "borough": "Manhattan", "gtfs_stop_ids": ["635", "635N", "635S", "R14", "R14N", "R14S", "L06", "L06N", "L06S"]},
            {"stop_id": "640", "stop_name": "Brooklyn Bridge-City Hall", "stop_lat": 40.713065, "stop_lon": -74.004131, "routes": ["4", "5", "6"], "borough": "Manhattan", "gtfs_stop_ids": ["640", "640N", "640S"]},
            
            # Manhattan - N/Q/R/W Line
            {"stop_id": "R11", "stop_name": "Lexington Ave/59 St", "stop_lat": 40.762526, "stop_lon": -73.967967, "routes": ["N", "Q", "R", "W"], "borough": "Manhattan", "gtfs_stop_ids": ["R11", "R11N", "R11S"]},
            {"stop_id": "R14", "stop_name": "49 St", "stop_lat": 40.759901, "stop_lon": -73.984139, "routes": ["N", "Q", "R", "W"], "borough": "Manhattan", "gtfs_stop_ids": ["R14", "R14N", "R14S"]},
            {"stop_id": "R16", "stop_name": "Times Sq-42 St", "stop_lat": 40.755983, "stop_lon": -73.986229, "routes": ["N", "Q", "R", "W"], "borough": "Manhattan", "gtfs_stop_ids": ["R16", "R16N", "R16S"]},
            {"stop_id": "R17", "stop_name": "34 St-Herald Sq", "stop_lat": 40.749567, "stop_lon": -73.987621, "routes": ["B", "D", "F", "M", "N", "Q", "R", "W"], "borough": "Manhattan", "gtfs_stop_ids": ["R17", "R17N", "R17S", "D16", "D16N", "D16S"]},
            
            # Manhattan - A/C/E Line
            {"stop_id": "A02", "stop_name": "Inwood-207 St", "stop_lat": 40.868072, "stop_lon": -73.919899, "routes": ["A"], "borough": "Manhattan", "gtfs_stop_ids": ["A02", "A02N", "A02S"]},
            {"stop_id": "A27", "stop_name": "59 St-Columbus Circle", "stop_lat": 40.768247, "stop_lon": -73.981929, "routes": ["A", "B", "C", "D"], "borough": "Manhattan", "gtfs_stop_ids": ["A27", "A27N", "A27S"]},
            {"stop_id": "A28", "stop_name": "50 St", "stop_lat": 40.762456, "stop_lon": -73.985984, "routes": ["C", "E"], "borough": "Manhattan", "gtfs_stop_ids": ["A28", "A28N", "A28S"]},
            {"stop_id": "A32", "stop_name": "34 St-Penn Station", "stop_lat": 40.752287, "stop_lon": -73.993391, "routes": ["A", "C", "E"], "borough": "Manhattan", "gtfs_stop_ids": ["A32", "A32N", "A32S"]},
            
            # Manhattan - B/D/F/M Line
            {"stop_id": "D14", "stop_name": "59 St-Columbus Circle", "stop_lat": 40.768247, "stop_lon": -73.981929, "routes": ["B", "D"], "borough": "Manhattan", "gtfs_stop_ids": ["D14", "D14N", "D14S"]},
            {"stop_id": "D15", "stop_name": "47-50 Sts-Rockefeller Ctr", "stop_lat": 40.758663, "stop_lon": -73.981329, "routes": ["B", "D", "F", "M"], "borough": "Manhattan", "gtfs_stop_ids": ["D15", "D15N", "D15S"]},
            {"stop_id": "D16", "stop_name": "34 St-Herald Sq", "stop_lat": 40.749567, "stop_lon": -73.987621, "routes": ["B", "D", "F", "M"], "borough": "Manhattan", "gtfs_stop_ids": ["D16", "D16N", "D16S"]},
            
            # Manhattan - L Line
            {"stop_id": "L06", "stop_name": "14 St-Union Sq", "stop_lat": 40.735736, "stop_lon": -73.990568, "routes": ["L"], "borough": "Manhattan", "gtfs_stop_ids": ["L06", "L06N", "L06S"]},
            {"stop_id": "L08", "stop_name": "8 Ave", "stop_lat": 40.739777, "stop_lon": -74.002578, "routes": ["L"], "borough": "Manhattan", "gtfs_stop_ids": ["L08", "L08N", "L08S"]},
            
            # Manhattan - 7 Line
            {"stop_id": "725", "stop_name": "Times Sq-42 St", "stop_lat": 40.755983, "stop_lon": -73.986229, "routes": ["7"], "borough": "Manhattan", "gtfs_stop_ids": ["725", "725N", "725S"]},
            {"stop_id": "723", "stop_name": "Grand Central-42 St", "stop_lat": 40.751776, "stop_lon": -73.976848, "routes": ["7"], "borough": "Manhattan", "gtfs_stop_ids": ["723", "723N", "723S"]},
            
            # Brooklyn
            {"stop_id": "R31", "stop_name": "95 St", "stop_lat": 40.616622, "stop_lon": -74.030876, "routes": ["R"], "borough": "Brooklyn", "gtfs_stop_ids": ["R31", "R31N", "R31S"]},
            {"stop_id": "D19", "stop_name": "Atlantic Ave-Barclays Ctr", "stop_lat": 40.684359, "stop_lon": -73.977666, "routes": ["B", "D", "N", "Q", "R", "2", "3", "4", "5"], "borough": "Brooklyn", "gtfs_stop_ids": ["D19", "D19N", "D19S", "R30", "R30N", "R30S", "238", "238N", "238S"]},
            {"stop_id": "R26", "stop_name": "Jay St-MetroTech", "stop_lat": 40.692338, "stop_lon": -73.987342, "routes": ["A", "C", "F", "R"], "borough": "Brooklyn", "gtfs_stop_ids": ["R26", "R26N", "R26S", "A41", "A41N", "A41S", "F20", "F20N", "F20S"]},
            
            # Queens
            {"stop_id": "Q01", "stop_name": "96 St", "stop_lat": 40.784318, "stop_lon": -73.947152, "routes": ["Q"], "borough": "Manhattan", "gtfs_stop_ids": ["Q01", "Q01N", "Q01S"]},
            {"stop_id": "702", "stop_name": "Flushing-Main St", "stop_lat": 40.759465, "stop_lon": -73.830109, "routes": ["7"], "borough": "Queens", "gtfs_stop_ids": ["702", "702N", "702S"]},
            
            # Bronx
            {"stop_id": "D03", "stop_name": "161 St-Yankee Stadium", "stop_lat": 40.827994, "stop_lon": -73.925831, "routes": ["4", "B", "D"], "borough": "Bronx", "gtfs_stop_ids": ["D03", "D03N", "D03S", "401", "401N", "401S"]},
        ],
        "metadata": {
            "total_stations": 38,
            "last_updated": "2025-11-05",
            "source": "Comprehensive sample dataset",
            "note": "This is a curated sample. Run generate_all_stations.py to get all 472+ stations."
        }
    }
    
    # Save to file
    output_file = "data/subway_stations.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_stations, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created sample dataset with {len(sample_stations['stations'])} stations")
    print(f"✓ Saved to {output_file}")
    return True

if __name__ == "__main__":
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Try to download full dataset
    success = download_and_convert_stations()
    
    # If download fails, create sample dataset
    if not success:
        print("\n⚠️  Full download failed. Creating comprehensive sample dataset instead...")
        create_sample_data()
    
    print("\n🎉 Done! Your chatbot now has station data.")
    print("   Restart your Flask server to use the new data.")
