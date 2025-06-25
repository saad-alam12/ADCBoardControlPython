#!/usr/bin/env python3
"""
Test script for the dual PSU service
Tests all endpoints without requiring actual hardware
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5001"

def test_endpoint(method, url, data=None, expected_status=200):
    """Test a single endpoint and return the result"""
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unknown method: {method}")
            return None
        
        print(f"{method} {url}")
        if data:
            print(f"  Data: {json.dumps(data)}")
        print(f"  Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"  Response: {json.dumps(result, indent=2)}")
        except:
            print(f"  Response: {response.text}")
        
        print()
        return response
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {url}")
        print("Make sure the dual PSU service is running with: python dual_psu_service.py")
        return None
    except Exception as e:
        print(f"ERROR testing {url}: {e}")
        return None

def main():
    print("Testing Dual PSU Service Endpoints")
    print("=" * 50)
    
    # Test root endpoint
    test_endpoint("GET", f"{BASE_URL}/")
    
    # Test status endpoint
    test_endpoint("GET", f"{BASE_URL}/status")
    
    # Test Heinzinger PSU endpoints
    print("Testing Heinzinger PSU endpoints:")
    test_endpoint("GET", f"{BASE_URL}/heinzinger/relay")
    test_endpoint("POST", f"{BASE_URL}/heinzinger/set_voltage", {"value": 1000.0})
    test_endpoint("POST", f"{BASE_URL}/heinzinger/set_current", {"value": 1.0})
    test_endpoint("GET", f"{BASE_URL}/heinzinger/read")
    test_endpoint("POST", f"{BASE_URL}/heinzinger/relay", {"state": True})
    test_endpoint("GET", f"{BASE_URL}/heinzinger/relay")
    test_endpoint("POST", f"{BASE_URL}/heinzinger/relay", {"state": False})
    
    # Test FUG PSU endpoints
    print("Testing FUG PSU endpoints:")
    test_endpoint("GET", f"{BASE_URL}/fug/relay")
    test_endpoint("POST", f"{BASE_URL}/fug/set_voltage", {"value": 2000.0})
    test_endpoint("POST", f"{BASE_URL}/fug/set_current", {"value": 0.3})
    test_endpoint("GET", f"{BASE_URL}/fug/read")
    test_endpoint("POST", f"{BASE_URL}/fug/relay", {"state": True})
    test_endpoint("GET", f"{BASE_URL}/fug/relay")
    test_endpoint("POST", f"{BASE_URL}/fug/relay", {"state": False})
    
    # Test error conditions
    print("Testing error conditions:")
    test_endpoint("POST", f"{BASE_URL}/heinzinger/set_voltage", {"value": 35000.0})  # Over limit
    test_endpoint("POST", f"{BASE_URL}/fug/set_current", {"value": 1.0})  # Over limit
    test_endpoint("POST", f"{BASE_URL}/invalid_psu/set_voltage", {"value": 1000.0})  # Invalid PSU
    
    # Final status check
    print("Final status check:")
    test_endpoint("GET", f"{BASE_URL}/status")

if __name__ == "__main__":
    main()
