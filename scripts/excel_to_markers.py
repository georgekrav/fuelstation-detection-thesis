# excel_to_markers 

import pandas as pd
from pathlib import Path
import json

EXCEL_PATH = Path("/Users/geo/Desktop/fuelstation-detection-thesis/data/ALL χιλιομετικές διευθύνσεις.xlsx")
OUT_JS = Path("data/markers.js")

df = pd.read_excel(EXCEL_PATH)

#  id, lat, lon, loc_type 

cols = [c.lower() for c in df.columns]

# Basikes stiles
id_col = "gasStationID"
lat_col = "gasStationLat" 
lon_col = "gasStationLong"

loc_type_col = "locationType"

rows = []
missing = []

# Epipleon stiles 
address_col = "gasStationAddress"
municipality_col = "municipalityName"
county_col = "countyName"

for _, r in df.iterrows():
    try:
        lat = float(r[lat_col])
        lon = float(r[lon_col])
    except Exception:
        missing.append({"row": r.to_dict(), "reason": "missing_coords"})
        continue
    
    station_id = str(r[id_col])
    loc_type = str(r[loc_type_col]) if pd.notna(r[loc_type_col]) else None
    address = str(r[address_col]) if pd.notna(r[address_col]) else None
    municipality = str(r[municipality_col]) if pd.notna(r[municipality_col]) else None
    county = str(r[county_col]) if pd.notna(r[county_col]) else None
    
    marker_data = {
        "id": station_id,
        "lat": lat,
        "lon": lon,
        "loc_type": loc_type,
        "address": address,
        "municipality": municipality,
        "county": county
    }
    
    rows.append(marker_data)

non_rooftop = [x for x in rows if x.get("loc_type") and x["loc_type"].strip().upper() != "ROOFTOP"]

OUT_JS.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_JS, "w", encoding="utf8") as f:
    f.write("// Auto-generated markers\n")
    f.write("const STATIONS = ")
    json.dump(rows, f, ensure_ascii=False, indent=2)
    f.write(";\n\n")
    f.write("const NON_ROOFTOP = ")
    json.dump(non_rooftop, f, ensure_ascii=False, indent=2)
    f.write(";\n\n")
    f.write("const MISSING_ROWS = ")
    json.dump(missing, f, ensure_ascii=False, indent=2)
    f.write(";\n")
print("Wrote", OUT_JS, "stations:", len(rows), "non_rooftop:", len(non_rooftop), "missing:", len(missing))