# -*- coding: utf-8 -*-
"""
Additional Geocoding Experiments - Καθηγητής Requests
Προσθέτει νέες μεθόδους στο existing geocoding_19methods_full.xlsx
"""

import os
import pandas as pd
import numpy as np
import re
from tqdm import tqdm
import time
import googlemaps
from math import radians, cos, sin, asin, sqrt
from dotenv import load_dotenv

# ============= CONFIGURATION =============
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

BASE_DIR = "/Users/geo/Desktop/fuelstation-detection-thesis/data/geocoding_pattern_analysis_ml"
EXISTING_RESULTS = os.path.join(BASE_DIR, "geocoding_19methods_full.xlsx")
OUTPUT_ENHANCED = os.path.join(BASE_DIR, "geocoding_enhanced_results.xlsx")

print("="*60)
print("ADDITIONAL GEOCODING EXPERIMENTS")
print("Requested by Professor")
print("="*60)

# ============= HELPER FUNCTIONS =============
def haversine_distance(lat1, lon1, lat2, lon2):
    """Υπολογισμός απόστασης σε μέτρα"""
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return None
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371000

# ============= NEW CLEANING METHODS (v20-v30) =============

def clean_v20_km_city1_city2(address):
    """v20: Format: [Αριθμός] Km [Πόλη1] [Πόλη2]"""
    km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    if km_match and len(cities) >= 2:
        km_num = km_match.group(1)
        return f"{km_num} Km {cities[0]} {cities[1]}"
    return address

def clean_v21_km_city1_city2_genitive(address):
    """v21: Format: [Αριθμός] Km [Πόλη1]ών [Πόλη2]ς"""
    km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    if km_match and len(cities) >= 2:
        km_num = km_match.group(1)
        # Προσθήκη γενικής πτώσης (simplified)
        city1_gen = cities[0] + "ών" if not cities[0].endswith('α') else cities[0][:-1] + "ών"
        city2_gen = cities[1] + "ς" if cities[1].endswith('α') else cities[1] + "ας"
        return f"{km_num} Km {city1_gen} {city2_gen}"
    return address

def clean_v22_km_eo_city1_city2(address):
    """v22: Format: [Αριθμός] Km Εθνικής Οδού [Πόλη1]ών [Πόλη2]ς"""
    km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    if km_match and len(cities) >= 2:
        km_num = km_match.group(1)
        city1_gen = cities[0] + "ών" if not cities[0].endswith('α') else cities[0][:-1] + "ών"
        city2_gen = cities[1] + "ς" if cities[1].endswith('α') else cities[1] + "ας"
        return f"{km_num} Km Εθνικής Οδού {city1_gen} {city2_gen}"
    return address

def clean_v23_city1_pros_city2(address):
    """v23: Format: [Πόλη1] προς [Πόλη2]"""
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    if len(cities) >= 2:
        km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
        if km_match:
            km_num = km_match.group(1)
            return f"{cities[0]} προς {cities[1]}, {km_num}ο χλμ"
        return f"{cities[0]} προς {cities[1]}"
    return address

def clean_v24_remove_all_prefixes(address):
    """v24: Αφαίρεση ΟΛΩΝ των prefixes (ΠΕΟ, ΕΟ, ΝΕΟ, ΟΔΟΣ, ΕΘΝΙΚΗΣ)"""
    # Πιο aggressive αφαίρεση
    patterns = [
        r'Π\.?\s?Ε\.?\s?Ο\.?',
        r'Ε\.?\s?Ο\.?',
        r'Ν\.?\s?Ε\.?\s?Ο\.?',
        r'ΠΕΟ|ΕΟ|ΝΕΟ',
        r'ΕΘΝΙΚΗΣ?\s+ΟΔΟΥ?',
        r'ΕΠΑΡΧΙΑΚΗ?\s+ΟΔΟΥ?',
        r'ΠΑΛΙΑ\s+ΕΘΝΙΚΗ?\s+ΟΔΟΥ?',
    ]
    
    for pattern in patterns:
        address = re.sub(pattern, '', address, flags=re.IGNORECASE)
    
    # Κανονικοποίηση χλμ
    address = re.sub(r'ΧΛΜ|χλμ|χιλ\.?|ΚΜ', 'χλμ', address, flags=re.IGNORECASE)
    address = re.sub(r'(\d+)[οηόήΟΗ]?\s+(χλμ)', r'\1ο χλμ', address)
    
    return ' '.join(address.split())

def clean_v25_big_cities_pattern(address):
    """v25: Pattern για μεγάλες πόλεις (Αθήνα, Θεσσαλονίκη, Πάτρα)"""
    big_cities = ['Αθήνα', 'Αθηνών', 'Θεσσαλονίκη', 'Θεσσαλονίκης', 'Πάτρα', 'Πατρών', 
                  'Λάρισα', 'Λαρίσης', 'Ηράκλειο', 'Ηρακλείου', 'Βόλος', 'Βόλου',
                  'Ιωάννινα', 'Ιωαννίνων', 'Χανιά', 'Χανίων', 'Λαμία', 'Λαμίας']
    
    km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
    
    # Βρες αν υπάρχει μεγάλη πόλη
    found_big_city = None
    for city in big_cities:
        if city in address:
            found_big_city = city
            break
    
    if found_big_city and km_match:
        km_num = km_match.group(1)
        # Βρες τη δεύτερη πόλη
        cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
        other_city = None
        for c in cities:
            if c != found_big_city and c not in ['ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ']:
                other_city = c
                break
        
        if other_city:
            return f"Εθνική Οδός {found_big_city} {other_city}, {km_num}ο χιλιόμετρο"
    
    return clean_v24_remove_all_prefixes(address)

def clean_v26_small_cities_pattern(address):
    """v26: Pattern για μικρές πόλεις"""
    km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    # Για μικρές πόλεις, χρησιμοποίησε πιο περιγραφικό format
    if km_match and len(cities) >= 2:
        km_num = km_match.group(1)
        return f"Επαρχιακή Οδός {cities[0]} - {cities[1]}, στο {km_num}ο χιλιόμετρο"
    
    return clean_v24_remove_all_prefixes(address)

def clean_v27_english_km_pattern(address):
    """v27: English pattern: Highway [City1]-[City2] km [number]"""
    km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    if km_match and len(cities) >= 2:
        km_num = km_match.group(1)
        return f"Highway {cities[0]}-{cities[1]} km {km_num}"
    
    return address

def clean_v28_nomoi_pattern(address):
    """v28: Προσθήκη νομού context"""
    cleaned = clean_v24_remove_all_prefixes(address)
    # Θα χρειαστεί το countyName από το DataFrame
    return cleaned  # Will be enhanced in the loop with county

def clean_v29_only_km_number(address):
    """v29: Μόνο χλμ και αριθμός για testing"""
    km_match = re.search(r'(\d+)[οηόήOH]?\s*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', address, re.IGNORECASE)
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    if km_match and len(cities) >= 1:
        km_num = km_match.group(1)
        return f"{km_num}ο χλμ {cities[0]}"
    
    return address

def clean_v30_inferred_highway(address):
    """v30: Προσπάθεια να συμπεράνει την εθνική οδό"""
    cities = re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)
    keywords = {'ΧΛΜ', 'Km', 'ΠΕΟ', 'ΕΟ', 'ΝΕΟ', 'ΟΔΟΣ', 'ΕΘΝΙΚΗΣ'}
    cities = [c for c in cities if c.upper() not in keywords]
    
    # Known highway patterns
    highway_map = {
        ('Αθήνα', 'Λαμία'): 'Α1',
        ('Αθήνα', 'Θεσσαλονίκη'): 'Α1', 
        ('Αθήνα', 'Κόρινθος'): 'Α8',
        ('Αθήνα', 'Πάτρα'): 'Α8',
        ('Λάρισα', 'Βόλος'): 'ΕΟ3',
        ('Θεσσαλονίκη', 'Καβάλα'): 'Α2',
    }
    
    if len(cities) >= 2:
        for (c1, c2), highway in highway_map.items():
            if (c1 in cities and c2 in cities) or (c2 in cities and c1 in cities):
                km_match = re.search(r'(\d+)', address)
                if km_match:
                    return f"{highway} {km_match.group(1)} km"
                return f"{highway} {cities[0]} {cities[1]}"
    
    return clean_v24_remove_all_prefixes(address)

# Dictionary με τις νέες μεθόδους
NEW_CLEANING_METHODS = {
    'v20_km_city1_city2': clean_v20_km_city1_city2,
    'v21_km_city1_city2_genitive': clean_v21_km_city1_city2_genitive,
    'v22_km_eo_city1_city2': clean_v22_km_eo_city1_city2,
    'v23_city1_pros_city2': clean_v23_city1_pros_city2,
    'v24_remove_all_prefixes': clean_v24_remove_all_prefixes,
    'v25_big_cities_pattern': clean_v25_big_cities_pattern,
    'v26_small_cities_pattern': clean_v26_small_cities_pattern,
    'v27_english_km_pattern': clean_v27_english_km_pattern,
    'v28_nomoi_pattern': clean_v28_nomoi_pattern,
    'v29_only_km_number': clean_v29_only_km_number,
    'v30_inferred_highway': clean_v30_inferred_highway,
}

print(f"\n✅ Ορίστηκαν {len(NEW_CLEANING_METHODS)} νέες μέθοδοι (v20-v30)")

# ============= MAIN EXECUTION =============

# Φόρτωση existing results
print(f"\n📂 Φόρτωση existing results από: {EXISTING_RESULTS}")
df_existing = pd.read_excel(EXISTING_RESULTS)
print(f"   Φορτώθηκαν {len(df_existing)} σταθμοί")
print(f"   Existing columns: {len(df_existing.columns)}")

# Προσθήκη νέων στηλών
print("\n🔄 Εκτέλεση νέων geocoding experiments...")
print(f"   API calls: {len(df_existing) * len(NEW_CLEANING_METHODS)}")
print(f"   Εκτιμώμενος χρόνος: ~{len(df_existing) * len(NEW_CLEANING_METHODS) * 0.1 / 60:.1f} λεπτά")

# Progress bar
for idx, row in tqdm(df_existing.iterrows(), total=len(df_existing), desc="New Geocoding"):
    
    for method_name, clean_func in NEW_CLEANING_METHODS.items():
        try:
            # Special handling για v28
            if method_name == 'v28_nomoi_pattern':
                cleaned_address = clean_v24_remove_all_prefixes(row['original_address'])
                cleaned_address = f"{cleaned_address}, Νομός {row['countyName']}"
            else:
                cleaned_address = clean_func(row['original_address'])
            
            # Geocoding query με county
            query = f"{cleaned_address}, {row['countyName']}, Greece"
            
            # API call
            result = gmaps.geocode(query, region='gr')
            
            if result:
                loc = result[0]['geometry']['location']
                distance = haversine_distance(
                    row['ground_truth_lat'], row['ground_truth_lng'],
                    loc['lat'], loc['lng']
                )
                accuracy = result[0]['geometry']['location_type']
                
                # Αποθήκευση αποτελεσμάτων
                df_existing.at[idx, f'{method_name}_address'] = cleaned_address
                df_existing.at[idx, f'{method_name}_lat'] = loc['lat']
                df_existing.at[idx, f'{method_name}_lng'] = loc['lng']
                df_existing.at[idx, f'{method_name}_distance'] = distance
                df_existing.at[idx, f'{method_name}_accuracy'] = accuracy
            else:
                # Αποτυχία geocoding
                df_existing.at[idx, f'{method_name}_address'] = cleaned_address
                df_existing.at[idx, f'{method_name}_distance'] = None
                df_existing.at[idx, f'{method_name}_accuracy'] = 'FAILED'
                
        except Exception as e:
            print(f"\n❌ Error για station {row['gasStationID']}, method {method_name}: {e}")
            df_existing.at[idx, f'{method_name}_address'] = cleaned_address
            df_existing.at[idx, f'{method_name}_distance'] = None
            df_existing.at[idx, f'{method_name}_accuracy'] = 'ERROR'
        
        # Rate limiting
        time.sleep(0.1)

# ============= FIND BEST METHOD OVERALL =============
print("\n📊 Υπολογισμός καλύτερης μεθόδου overall...")

# Συλλογή όλων των μεθόδων (παλιές + νέες)
all_methods = []

# Βρες όλες τις μεθόδους από τις στήλες
for col in df_existing.columns:
    if col.endswith('_distance') and not col.startswith('best_') and not col.startswith('original_'):
        method_name = col.replace('_distance', '')
        all_methods.append(method_name)

print(f"   Συνολικές μέθοδοι: {len(all_methods)}")

# Υπολογισμός best method για κάθε σταθμό
def find_best_method_enhanced(row):
    """Βρίσκει την καλύτερη μέθοδο για κάθε σταθμό"""
    best_method = None
    best_distance = float('inf')
    
    for method in all_methods:
        dist_col = f'{method}_distance'
        if dist_col in row and pd.notna(row[dist_col]) and row[dist_col] < best_distance:
            best_distance = row[dist_col]
            best_method = method
    
    return pd.Series({
        'best_method_enhanced': best_method,
        'best_distance_enhanced': best_distance,
        'improvement_over_v1': row['v1_original_distance'] - best_distance if best_method else 0
    })

# Εφαρμογή
best_results_enhanced = df_existing.apply(find_best_method_enhanced, axis=1)
df_final = pd.concat([df_existing, best_results_enhanced], axis=1)

# ============= STATISTICS & RANKING =============
print("\n📈 Στατιστικά ανά μέθοδο:")

stats_data = []
for method in all_methods:
    dist_col = f'{method}_distance'
    if dist_col in df_final.columns:
        distances = df_final[dist_col].dropna()
        
        if len(distances) > 0:
            stats_data.append({
                'Method': method,
                'Mean_Distance_m': distances.mean(),
                'Median_Distance_m': distances.median(),
                'Success_Rate_%': (len(distances) / len(df_final)) * 100,
                'Within_100m_%': (distances <= 100).mean() * 100,
                'Within_500m_%': (distances <= 500).mean() * 100,
                'Times_Best': (df_final['best_method_enhanced'] == method).sum()
            })

stats_df = pd.DataFrame(stats_data).sort_values('Mean_Distance_m')

print("\n🏆 TOP 10 Μέθοδοι (by mean distance):")
print(stats_df[['Method', 'Mean_Distance_m', 'Within_100m_%', 'Times_Best']].head(10).to_string(index=False))

# ============= SAVE RESULTS =============
print(f"\n💾 Αποθήκευση enhanced results στο: {OUTPUT_ENHANCED}")
df_final.to_excel(OUTPUT_ENHANCED, index=False)

# Αποθήκευση και των statistics
STATS_OUTPUT = os.path.join(BASE_DIR, "geocoding_methods_statistics.xlsx")
stats_df.to_excel(STATS_OUTPUT, index=False)
print(f"   Statistics αποθηκεύτηκαν στο: {STATS_OUTPUT}")

# ============= FINAL SUMMARY =============
print("\n" + "="*60)
print("ΣΥΝΟΨΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ")
print("="*60)

# Overall improvements
original_mean = df_final['v1_original_distance'].mean()
best_mean = df_final['best_distance_enhanced'].mean()
improvement_pct = ((original_mean - best_mean) / original_mean) * 100

print(f"\n📍 Μέση απόσταση:")
print(f"   Original (v1): {original_mean:.1f} m")
print(f"   Best method:   {best_mean:.1f} m")
print(f"   Βελτίωση:      {improvement_pct:.1f}%")

# Best performing new methods
new_methods_performance = stats_df[stats_df['Method'].str.startswith('v2')].head(5)
if not new_methods_performance.empty:
    print(f"\n🌟 Καλύτερες νέες μέθοδοι (v20-v30):")
    print(new_methods_performance[['Method', 'Mean_Distance_m', 'Times_Best']].to_string(index=False))

print("\n✅ Script ολοκληρώθηκε επιτυχώς!")
print(f"   Enhanced dataset: {OUTPUT_ENHANCED}")
print(f"   Statistics: {STATS_OUTPUT}")
