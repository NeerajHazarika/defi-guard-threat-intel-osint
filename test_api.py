#!/usr/bin/env python3
"""
Test script for DeFi Guard OSINT API
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test the health check endpoint"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data['message']}")
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False

async def test_threat_intel_endpoint():
    """Test the threat intelligence endpoint"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/api/v1/threat-intel?limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Threat intel endpoint working: {data['count']} items returned")
                    if data['count'] > 0:
                        item = data['data'][0]
                        print(f"   Sample item: {item['title'][:50]}...")
                    return True
                else:
                    print(f"❌ Threat intel endpoint failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Threat intel endpoint error: {str(e)}")
            return False

async def test_sources_endpoint():
    """Test the sources endpoint"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/api/v1/sources") as response:
                if response.status == 200:
                    data = await response.json()
                    sources = data.get('sources', [])
                    print(f"✅ Sources endpoint working: {len(sources)} sources available")
                    print(f"   Available sources: {', '.join(sources)}")
                    return True
                else:
                    print(f"❌ Sources endpoint failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Sources endpoint error: {str(e)}")
            return False

async def test_stats_endpoint():
    """Test the statistics endpoint"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/api/v1/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get('stats', {})
                    print(f"✅ Stats endpoint working")
                    print(f"   Total incidents: {stats.get('total_incidents', 0)}")
                    print(f"   Total amount lost: ${stats.get('total_amount_lost', 0):,.2f}")
                    return True
                else:
                    print(f"❌ Stats endpoint failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Stats endpoint error: {str(e)}")
            return False

async def test_scrape_endpoint():
    """Test the manual scrape endpoint"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE_URL}/api/v1/scrape") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Scrape endpoint working: {data['message']}")
                    return True
                else:
                    print(f"❌ Scrape endpoint failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Scrape endpoint error: {str(e)}")
            return False

async def test_filtering():
    """Test various filtering options"""
    async with aiohttp.ClientSession() as session:
        test_filters = [
            ("risk_level=high", "high risk filter"),
            ("limit=3", "limit filter"),
            ("source=rekt", "source filter"),
        ]
        
        all_passed = True
        for filter_param, description in test_filters:
            try:
                url = f"{API_BASE_URL}/api/v1/threat-intel?{filter_param}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {description}: {data['count']} items")
                    else:
                        print(f"❌ {description} failed: HTTP {response.status}")
                        all_passed = False
            except Exception as e:
                print(f"❌ {description} error: {str(e)}")
                all_passed = False
        
        return all_passed

async def main():
    """Run all tests"""
    print("=== DeFi Guard OSINT API Test Suite ===\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Threat Intel Endpoint", test_threat_intel_endpoint),
        ("Sources Endpoint", test_sources_endpoint),
        ("Statistics Endpoint", test_stats_endpoint),
        ("Manual Scrape Endpoint", test_scrape_endpoint),
        ("Filtering Tests", test_filtering),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the API configuration.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
