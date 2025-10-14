# From Geocoding to Computer Vision: Locating Greek Fuel Stations

Demonstrating Geocoding limitations and proposing a computer-vision-based solution.
This thesis investigates the reliability of geocoding for Greek fuel station addresses and proposes an alternative approach using computer vision. The project consists of two main phases:

## Phase 1 - Geocoding Analysis:

Dataset: 1026 fuel stations across Greece with **verified ground truth coordinates**                        
Comprehensive Testing: 17 different address preprocessing methods including:

1. v1_original = no change(same from the dataset)
2. v2_remove_prefix = remove Π.E.O., E.O., N.E.O.  
3. v3_normalize_km = convert ΧΛΜ to Km  
4. v4_remove_punct = remove -, ?, ,  
5. v5_remove_dots = remove dots  
6. v6_remove_all_punct = remove all punctuation  
7. v7_combined_basic = combination of v2 + v3 + v5  
8. v8_combined_aggressive = combination of v2 + v3 + v5 + v6  
9. v9_add_eo_prefix = add “Ethniki Odos” (national road) at the beginning  
10. v10_km_first = Km first in order  
11. v11_simplify_cities_only = cities only (simplified)  
12. v12_simplify_km_cities = Km and cities only  
13. v13_add_greece_suffix = add “Greece” at the end  
14. v14_add_highway_context = add “highway” at the beginning  
15. v15_english_translation = translate to English (where possible)  
16. v16_lowercase_normalized = lowercase  
17. v17_uppercase_normalized = uppercase  

Performance Evaluation:Metric analysis **revealing geocoding failures** :

1. Circular Error metrics (CE50, CE100, CE500, CE1000)
2. Mean distances often exceeding **14km from actual location**
3. **Despite 99.03% "success rate", ROOFTOP accuracy as low as 1.8-3.7%**
4. **Maximum errors reaching 300+ kilometers**

Machine learning analysis:

Random Forest classifier to identify optimal preprocessing per address type. 13 engineered features revealing address pattern complexity
Results show that even machine learning-optimized preprocessing cannot achieve reliable accuracy.

Critical Finding:
### While preprocessing improves results a little, geocoding fundamentally **fails for Greek highway addresses**. The high "success rate" hide poor actual accuracy with typical errors of 5-15km making the approach unsuitable for precise location requirements.

## Phase 2 - Computer Vision Solution (not finished yet)

**Given the proven weakness of geocoding, this phase explores the use of:**

1. Satellite images detection
2. Street-level image recognition
3. Deep learning models for fuel station recognision
4. Integration with geocoding data for validation (not sure yet..)

