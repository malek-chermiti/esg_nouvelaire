#!/usr/bin/env python
"""Create a fresh anomaly and observe AIService generation."""

import requests
import json
import time

# Test with a year that should have fresh data (or at least different anomalies)
# We'll also clear the anomalies for that year first if needed

year = 2025

print("=" * 70)
print(f"Testing fresh anomaly detection for year {year}")
print("=" * 70)

# Test different KPIs
kpis = ['CO2', 'FORMATION', 'LTIR']

for kpi in kpis:
    print(f"\nTesting {kpi} ({year})...")
    
    response = requests.post(
        f'http://127.0.0.1:8000/api/anomalies/detect/{kpi}',
        params={'year': year}
    )
    
    if response.status_code == 200:
        anomalies = response.json()
        print(f"  Anomalies found: {len(anomalies)}")
        
        if anomalies:
            # We have anomalies - now test the newest one
            newest = anomalies[0]
            anomaly_id = newest['id']
            print(f"  Newest anomaly ID: {anomaly_id}")
            
            # Wait a bit for the async operations
            time.sleep(1)
            
            # Check for recommendation
            rec_response = requests.get(
                f'http://127.0.0.1:8000/api/anomalies/{anomaly_id}/recommendation'
            )
            
            if rec_response.status_code == 200:
                print(f"  ✓ RECOMMENDATION FOUND!")
                rec = rec_response.json()
                print(json.dumps(rec, indent=4, ensure_ascii=False))
                break  # Found a working one
            else:
                print(f"  ✗ No recommendation (status={rec_response.status_code})")
    else:
        print(f"  Error: {response.status_code}")
