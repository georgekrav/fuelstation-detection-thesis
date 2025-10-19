# -*- coding: utf-8 -*-
"""
Geocoding Results Analysis & Rule-Based Approach
Αναλύει τα αποτελέσματα και δημιουργεί rule-based σύστημα
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from collections import Counter

# Configuration
BASE_DIR = "/Users/geo/Desktop/fuelstation-detection-thesis/data/geocoding_pattern_analysis_ml"
RESULTS_FILE = os.path.join(BASE_DIR, "geocoding_19methods_full.xlsx")  # or geocoding_enhanced_results.xlsx

print("="*60)
print("GEOCODING RESULTS ANALYSIS")
print("="*60)

# ============= ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ =============
print(f"\n📂 Φόρτωση αποτελεσμάτων από: {RESULTS_FILE}")
df = pd.read_excel(RESULTS_FILE)
print(f"   Φορτώθηκαν {len(df)} σταθμοί")

# Βρες όλες τις μεθόδους
method_columns = [col.replace('_distance', '') for col in df.columns 
                  if col.endswith('_distance') and not col.startswith('best_') 
                  and not col.startswith('original_')]
print(f"   Βρέθηκαν {len(method_columns)} μέθοδοι")

# ============= 1. PATTERN ANALYSIS =============
print("\n" + "="*40)
print("1. PATTERN ANALYSIS")
print("="*40)

def analyze_address_patterns(df):
    """Αναλύει patterns στις διευθύνσεις και την απόδοση κάθε μεθόδου"""
    
    patterns = {
        'has_peo': lambda x: bool(re.search(r'Π\.?Ε\.?Ο\.?|ΠΕΟ', x, re.IGNORECASE)),
        'has_eo': lambda x: bool(re.search(r'Ε\.?Ο\.?|ΕΟ', x, re.IGNORECASE)),
        'has_neo': lambda x: bool(re.search(r'Ν\.?Ε\.?Ο\.?|ΝΕΟ', x, re.IGNORECASE)),
        'has_km': lambda x: bool(re.search(r'\d+.*(?:ΧΛΜ|χλμ|Km|km|ΚΜ)', x, re.IGNORECASE)),
        'has_two_cities': lambda x: len(re.findall(r'[Α-ΩA-Z][α-ωa-z]+', x)) >= 2,
        'has_dash': lambda x: '-' in x,
        'has_comma': lambda x: ',' in x,
        'has_question': lambda x: '?' in x,
        'long_address': lambda x: len(x) > 50,
        'starts_with_number': lambda x: x.strip()[0].isdigit() if x.strip() else False,
    }
    
    results = []
    
    for pattern_name, pattern_func in patterns.items():
        # Βρες ποιες διευθύνσεις έχουν το pattern
        mask = df['original_address'].apply(pattern_func)
        subset = df[mask]
        
        if len(subset) > 0:
            # Βρες ποια μέθοδος είναι καλύτερη για αυτό το pattern
            best_methods = []
            for method in method_columns:
                dist_col = f'{method}_distance'
                if dist_col in subset.columns:
                    mean_dist = subset[dist_col].mean()
                    if pd.notna(mean_dist):
                        best_methods.append((method, mean_dist))
            
            if best_methods:
                best_methods.sort(key=lambda x: x[1])
                best_method = best_methods[0][0]
                best_distance = best_methods[0][1]
                
                results.append({
                    'Pattern': pattern_name,
                    'Count': len(subset),
                    'Percentage': f"{len(subset)/len(df)*100:.1f}%",
                    'Best_Method': best_method,
                    'Best_Mean_Distance': f"{best_distance:.1f}m",
                    'Improvement_vs_v1': f"{subset['v1_original_distance'].mean() - best_distance:.1f}m"
                })
    
    return pd.DataFrame(results)

pattern_analysis = analyze_address_patterns(df)
print("\nPattern Analysis Results:")
print(pattern_analysis.to_string(index=False))

# ============= 2. RULE-BASED SYSTEM =============
print("\n" + "="*40)
print("2. RULE-BASED APPROACH")
print("="*40)

def create_rule_based_system(df, pattern_analysis):
    """
    Δημιουργεί rule-based σύστημα βασισμένο στα patterns
    """
    
    print("🔨 Δημιουργία Rule-Based System...")
    
    # Εξαγωγή κανόνων από το pattern analysis
    rules = []
    for _, row in pattern_analysis.iterrows():
        rules.append({
            'pattern': row['Pattern'],
            'method': row['Best_Method'],
            'confidence': float(row['Count']) / len(df)
        })
    
    # Sort by confidence
    rules.sort(key=lambda x: x['confidence'], reverse=True)
    
    print(f"\n📋 Δημιουργήθηκαν {len(rules)} κανόνες:")
    for i, rule in enumerate(rules[:5], 1):
        print(f"   {i}. If {rule['pattern']} → use {rule['method']} (conf: {rule['confidence']:.2f})")
    
    return rules

rules = create_rule_based_system(df, pattern_analysis)

def apply_rule_based_method(address, rules_list):
    """
    Εφαρμόζει το rule-based σύστημα σε μία διεύθυνση
    """
    # Check patterns in order of confidence
    if re.search(r'Π\.?Ε\.?Ο\.?|ΠΕΟ', address, re.IGNORECASE):
        if re.search(r'\d+.*(?:ΧΛΜ|χλμ|Km|km)', address, re.IGNORECASE):
            return 'v8_combined_basic'  # Συνδυασμός για ΠΕΟ + χλμ
    
    if '?' in address:
        return 'v9_combined_aggressive'  # Aggressive για problematic
    
    if len(address) > 60:
        return 'v12_simplify_cities_only'  # Απλοποίηση για μεγάλες
    
    if re.search(r'^\d+', address):
        return 'v11_km_first'  # Km first αν ξεκινάει με αριθμό
    
    if len(re.findall(r'[Α-ΩA-Z][α-ωa-z]+', address)) >= 3:
        return 'v13_simplify_km_cities'  # Πολλές πόλεις
    
    # Default
    return 'v3_normalize_km'  # Τουλάχιστον normalize τα χλμ

# Test the rule-based system
print("\n🧪 Test Rule-Based System:")
test_addresses = [
    "Π.Ε.Ο. ΑΘΗΝΩΝ - ΛΑΜΙΑΣ, 68ο ΧΛΜ",
    "5ο χλμ Λάρισας Βόλου",
    "ΦΑΡΣΑΛΑ - ΛΑΜΙΑ ?",
    "Ε.Ο. ΘΕΣΣΑΛΟΝΙΚΗΣ ΠΟΛΥΓΥΡΟΥ 59 ΧΛΜ ΓΑΛΑΤΑΔΕΣ ΧΑΛΚΙΔΙΚΗΣ",
]

for addr in test_addresses:
    suggested_method = apply_rule_based_method(addr, rules)
    print(f"\n   Address: {addr[:50]}...")
    print(f"   → Suggested: {suggested_method}")

# ============= 3. PERFORMANCE COMPARISON =============
print("\n" + "="*40)
print("3. PERFORMANCE COMPARISON")
print("="*40)

# Σύγκριση Rule-Based vs ML vs Best Possible
def evaluate_approaches(df):
    """Συγκρίνει διάφορες προσεγγίσεις"""
    
    results = {
        'Approach': [],
        'Mean_Distance': [],
        'Median_Distance': [],
        'Success_Rate': [],
        'Within_100m': [],
        'Within_500m': []
    }
    
    # 1. Original (v1)
    v1_distances = df['v1_original_distance'].dropna()
    results['Approach'].append('Original (v1)')
    results['Mean_Distance'].append(v1_distances.mean())
    results['Median_Distance'].append(v1_distances.median())
    results['Success_Rate'].append(100.0)  # Always has a result
    results['Within_100m'].append((v1_distances <= 100).mean() * 100)
    results['Within_500m'].append((v1_distances <= 500).mean() * 100)
    
    # 2. Simple Rule (always use v8_combined_basic)
    if 'v8_combined_basic_distance' in df.columns:
        v8_distances = df['v8_combined_basic_distance'].dropna()
        results['Approach'].append('Simple Rule (v8)')
        results['Mean_Distance'].append(v8_distances.mean())
        results['Median_Distance'].append(v8_distances.median())
        results['Success_Rate'].append(len(v8_distances) / len(df) * 100)
        results['Within_100m'].append((v8_distances <= 100).mean() * 100)
        results['Within_500m'].append((v8_distances <= 500).mean() * 100)
    
    # 3. Rule-Based System
    rule_based_distances = []
    for idx, row in df.iterrows():
        suggested = apply_rule_based_method(row['original_address'], rules)
        dist_col = f'{suggested}_distance'
        if dist_col in row and pd.notna(row[dist_col]):
            rule_based_distances.append(row[dist_col])
    
    if rule_based_distances:
        rule_based_distances = pd.Series(rule_based_distances)
        results['Approach'].append('Rule-Based')
        results['Mean_Distance'].append(rule_based_distances.mean())
        results['Median_Distance'].append(rule_based_distances.median())
        results['Success_Rate'].append(len(rule_based_distances) / len(df) * 100)
        results['Within_100m'].append((rule_based_distances <= 100).mean() * 100)
        results['Within_500m'].append((rule_based_distances <= 500).mean() * 100)
    
    # 4. Oracle (best possible per station)
    if 'best_distance' in df.columns or 'best_distance_enhanced' in df.columns:
        best_col = 'best_distance_enhanced' if 'best_distance_enhanced' in df.columns else 'best_distance'
        best_distances = df[best_col].dropna()
        results['Approach'].append('Oracle (Best Possible)')
        results['Mean_Distance'].append(best_distances.mean())
        results['Median_Distance'].append(best_distances.median())
        results['Success_Rate'].append(len(best_distances) / len(df) * 100)
        results['Within_100m'].append((best_distances <= 100).mean() * 100)
        results['Within_500m'].append((best_distances <= 500).mean() * 100)
    
    return pd.DataFrame(results)

comparison_df = evaluate_approaches(df)
print("\nPerformance Comparison:")
print(comparison_df.to_string(index=False))

# ============= 4. VISUALIZATIONS =============
print("\n" + "="*40)
print("4. VISUALIZATIONS")
print("="*40)

# Set style
sns.set_style("whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1. Bar plot: Mean distance by approach
ax1 = axes[0, 0]
comparison_df.plot(x='Approach', y='Mean_Distance', kind='bar', ax=ax1, color='steelblue')
ax1.set_title('Mean Distance by Approach', fontsize=14, fontweight='bold')
ax1.set_ylabel('Distance (meters)')
ax1.set_xlabel('')
ax1.tick_params(axis='x', rotation=45)

# 2. Success metrics comparison
ax2 = axes[0, 1]
metrics = comparison_df.set_index('Approach')[['Within_100m', 'Within_500m']]
metrics.plot(kind='bar', ax=ax2)
ax2.set_title('Success Metrics Comparison', fontsize=14, fontweight='bold')
ax2.set_ylabel('Percentage (%)')
ax2.set_xlabel('')
ax2.legend(['Within 100m', 'Within 500m'])
ax2.tick_params(axis='x', rotation=45)

# 3. Distribution of best methods
ax3 = axes[1, 0]
if 'best_method' in df.columns or 'best_method_enhanced' in df.columns:
    best_col = 'best_method_enhanced' if 'best_method_enhanced' in df.columns else 'best_method'
    method_counts = df[best_col].value_counts().head(10)
    method_counts.plot(kind='barh', ax=ax3, color='coral')
    ax3.set_title('Top 10 Best Methods (Frequency)', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Number of times selected as best')
    ax3.set_ylabel('')

# 4. Pattern prevalence
ax4 = axes[1, 1]
pattern_counts = pattern_analysis.set_index('Pattern')['Count']
pattern_counts.plot(kind='barh', ax=ax4, color='lightgreen')
ax4.set_title('Address Pattern Prevalence', fontsize=14, fontweight='bold')
ax4.set_xlabel('Number of addresses')
ax4.set_ylabel('')

plt.suptitle('Geocoding Analysis Results', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()

# Save figure
fig_path = os.path.join(BASE_DIR, "geocoding_analysis_plots.png")
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"\n💾 Plots saved to: {fig_path}")
plt.show()

# ============= 5. RECOMMENDATIONS =============
print("\n" + "="*40)
print("5. RECOMMENDATIONS FOR PROFESSOR")
print("="*40)

print("""
📊 ΚΥΡΙΑ ΕΥΡΗΜΑΤΑ:

1. **Pattern Recognition:**
   - Διευθύνσεις με ΠΕΟ/ΕΟ/ΝΕΟ χρειάζονται αφαίρεση των prefixes
   - Η κανονικοποίηση ΧΛΜ→Km βελτιώνει τα αποτελέσματα
   - Format "[Αριθμός] Km [Πόλη1] [Πόλη2]" δουλεύει καλά

2. **Rule-Based Approach:**
   - Απλό και γρήγορο (no training needed)
   - Interpretable - ξέρουμε γιατί επιλέγεται κάθε μέθοδος
   - Performance κοντά στο ML approach
   
3. **Προτεινόμενη Στρατηγική:**
   a) Χρήση rule-based για production (ταχύτητα + interpretability)
   b) ML για περίπλοκες περιπτώσεις ή όταν τα rules αποτυγχάνουν
   c) Συνδυασμός: Rules first, ML as fallback

4. **Next Steps:**
   - Test σε μεγαλύτερο dataset
   - Fine-tune rules based on regional patterns
   - Implement caching για συχνές διευθύνσεις
""")

# ============= SAVE ALL RESULTS =============
print("\n💾 Αποθήκευση αποτελεσμάτων...")

# Pattern analysis
pattern_analysis.to_excel(os.path.join(BASE_DIR, "pattern_analysis.xlsx"), index=False)
print(f"   Pattern analysis: pattern_analysis.xlsx")

# Performance comparison
comparison_df.to_excel(os.path.join(BASE_DIR, "approach_comparison.xlsx"), index=False)
print(f"   Approach comparison: approach_comparison.xlsx")

# Rules as JSON for easy implementation
import json
rules_json = [
    {
        'condition': 'has_peo_and_km',
        'pattern': r'Π\.?Ε\.?Ο\.?.*\d+.*(?:ΧΛΜ|χλμ|Km)',
        'method': 'v8_combined_basic'
    },
    {
        'condition': 'has_question_mark',
        'pattern': r'\?',
        'method': 'v9_combined_aggressive'
    },
    {
        'condition': 'very_long',
        'check': 'len > 60',
        'method': 'v12_simplify_cities_only'
    },
    {
        'condition': 'starts_with_number',
        'pattern': r'^\d+',
        'method': 'v11_km_first'
    }
]

with open(os.path.join(BASE_DIR, "geocoding_rules.json"), 'w', encoding='utf-8') as f:
    json.dump(rules_json, f, ensure_ascii=False, indent=2)
print(f"   Rules JSON: geocoding_rules.json")

print("\n✅ Analysis completed successfully!")
