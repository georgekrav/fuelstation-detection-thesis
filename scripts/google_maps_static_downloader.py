import pandas as pd
import requests
import os
from pathlib import Path
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Parametroi
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 640
ZOOM_LEVEL = 19
OUTPUT_FOLDER = "/Users/geo/Desktop/fuelstation-detection-thesis/dataset/all"
MAP_TYPE = 'satellite'
SHOW_MARKER = False

def load_all_stations(file_path):
    print(f"Fortosi dedomenon apo: {file_path}")
    df = pd.read_excel(file_path)
    print(f"Synolo pratirion: {len(df)}")
    
    required_cols = ['gasStationID', 'gasStationLat', 'gasStationLong']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Leipei i stili: {col}")
    
    return df

def get_static_map_url(lat, lon, zoom, width, height, api_key, map_type='satellite', show_marker=False):
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    url = (
        f"{base_url}?"
        f"center={lat},{lon}&"
        f"zoom={zoom}&"
        f"size={width}x{height}&"
        f"scale=1&"
        f"maptype={map_type}&"
    )
    if show_marker:
        url += f"markers=color:red|{lat},{lon}&"
    url += f"key={api_key}"
    return url

def download_map_image(url, output_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                file_size = os.path.getsize(output_path)
                if file_size < 1000:
                    print(f"   Mikro megethos arxeiou ({file_size} bytes)")
                    return False
                return True
            else:
                print(f"   Sfalma: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   Prospatheia {attempt+1}/{max_retries} apetyche: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    return False

def create_all_images(data_file, api_key, output_folder):
    #  leitourgia katevamatos eikonon
    print("="*70)
    print(" Google Maps Static API - Lipsi Eikonon")
    print("="*70)
    print()
    
    if not api_key:
        print("Sfalma: Den vrethike API key")
        return
    
    print(f"API Key: {api_key[:20]}...")
    
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Fakelos exodou: {output_path.absolute()}")
    print()
    
    try:
        stations_df = load_all_stations(data_file)
    except Exception as e:
        print(f"Sfalma fortosis: {e}")
        return
    
    print()
    print(f"Katevasma eikonon:")
    print(f"   Megethos: {IMAGE_WIDTH}x{IMAGE_HEIGHT} pixels")
    print(f"   Typos charti: {MAP_TYPE}")
    print(f"   Marker: {'Nai' if SHOW_MARKER else 'Ochi'}")
    print(f"   Zoom level: {ZOOM_LEVEL}")
    print(f"   Synolo eikonon: {len(stations_df)}")
    print()
    
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0
    }
    
    log_data = []
    
    for idx, row in stations_df.iterrows():
        station_id = row['gasStationID']
        lat = row['gasStationLat']
        lon = row['gasStationLong']
        
        print(f"Pratirio {idx+1}/{len(stations_df)}: ID={station_id}")
        print(f"  Thesi: {lat:.6f}, {lon:.6f}")
        
        stats['total'] += 1
        
        padded_id = str(station_id).zfill(5)
        filename = f"{padded_id}_zoom_{ZOOM_LEVEL}_{IMAGE_WIDTH}x{IMAGE_HEIGHT}.png"
        filepath = output_path / filename
        
        url = get_static_map_url(lat, lon, ZOOM_LEVEL, IMAGE_WIDTH, IMAGE_HEIGHT, 
                                api_key, MAP_TYPE, SHOW_MARKER)
        
        print(f"  Lipsi zoom {ZOOM_LEVEL} ({IMAGE_WIDTH}x{IMAGE_HEIGHT})...", end=" ")
        success = download_map_image(url, filepath)
        
        if success:
            print("OK")
            stats['success'] += 1
            status = 'success'
        else:
            print("Apotychia")
            stats['failed'] += 1
            status = 'failed'
        
        log_data.append({
            'station_id': station_id,
            'lat': lat,
            'lon': lon,
            'zoom': ZOOM_LEVEL,
            'resolution': f"{IMAGE_WIDTH}x{IMAGE_HEIGHT}",
            'filename': filename,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
        time.sleep(0.5)
        
        if (idx + 1) % 10 == 0:
            print()
    
    log_df = pd.DataFrame(log_data)
    log_file = output_path / 'download_log.csv'
    log_df.to_csv(log_file, index=False)
    print(f"\nLog: {log_file}")
    print()
    
    print("="*70)
    print(" Perilipsi")
    print("="*70)
    print(f"Synolo eikonon: {stats['total']}")
    print(f"Epitychis lipsi: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"Apotychies: {stats['failed']}")
    print()
    print(f"Arxeia: {output_path.absolute()}")
    print()

if __name__ == "__main__":
    DATA_FILE = "/Users/geo/Desktop/fuelstation-detection-thesis/data/ALL χιλιομετικές διευθύνσεις.xlsx"
    
    if not GOOGLE_API_KEY:
        print("="*70)
        print(" Sfalma: Den vrethike API Key")
        print("="*70)
        print()
        print("Orise to GOOGLE_MAPS_API_KEY sto .env file")
        print("="*70)
        exit(1)
    
    create_all_images(
        data_file=DATA_FILE,
        api_key=GOOGLE_API_KEY,
        output_folder=OUTPUT_FOLDER
    )
    
    print()
    print("="*70)
    print(" Oloklirothike")
    print("="*70)
    print()