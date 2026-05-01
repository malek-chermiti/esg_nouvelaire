#!/usr/bin/env python
"""Test the complete anomaly detection and recommendation flow."""

import requests
import json
import time

def test_flow():
    """Test POST /detect/{kpi_code} and GET /recommendation"""
    
    # Give server time to initialize
    time.sleep(2)
    
    # Test 1: POST /detect/WASTE
    print("=" * 60)
    print("TEST 1: POST /detect/WASTE")
    print("=" * 60)
    
    response = requests.post('http://127.0.0.1:8000/api/anomalies/detect/WASTE', params={'year': 2024})
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        anomalies = response.json()
        print(f'✓ Anomalies found: {len(anomalies)}')
        
        if anomalies:
            first_anomaly = anomalies[0]
            anomaly_id = first_anomaly['id']
            print(f'  - First anomaly ID: {anomaly_id}')
            print(f'  - Severity: {first_anomaly.get("severity", "N/A")}')
            print(f'  - Description: {first_anomaly.get("description", "N/A")}')
            
            # Test 2: GET /anomalies/{anomaly_id}/recommendation
            print("\n" + "=" * 60)
            print("TEST 2: GET /anomalies/{anomaly_id}/recommendation")
            print("=" * 60)
            
            rec_response = requests.get(f'http://127.0.0.1:8000/api/anomalies/{anomaly_id}/recommendation')
            print(f'Status: {rec_response.status_code}')
            
            if rec_response.status_code == 200:
                rec_data = rec_response.json()
                print("✓ Recommendation retrieved successfully!")
                print(json.dumps(rec_data, indent=2, ensure_ascii=False))
            elif rec_response.status_code == 404:
                print("✗ No recommendation found (404)")
                print("  This might mean AIService.generate_recommendation() was not called or failed silently")
            else:
                print(f"✗ Error: {rec_response.status_code}")
                print(rec_response.text)
        else:
            print("✗ No anomalies detected")
            print("  This could mean there's no data or the detection logic didn't trigger")
    else:
        print(f'✗ Error: {response.status_code}')
        print(response.text)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_flow()
