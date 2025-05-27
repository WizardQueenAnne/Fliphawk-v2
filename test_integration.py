#!/usr/bin/env python3
"""
FlipHawk Test Script
Test the eBay Browse API integration and Flask app
"""

import sys
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ebay_api():
    """Test the eBay API integration"""
    
    print("🚀 FlipHawk eBay API Test")
    print("=" * 50)
    
    try:
        # Import our eBay API module
        from ebay_api_v2 import search_ebay, get_categories, ebay_api
        
        print("✅ Successfully imported eBay API module")
        
        # Test API credentials
        print("\n🔑 Testing OAuth access token...")
        token = ebay_api.get_access_token()
        if token:
            print(f"✅ Access token obtained: {token[:20]}...")
        else:
            print("❌ Failed to get access token")
            return False
        
        # Test simple search
        print("\n🔍 Testing search functionality...")
        test_searches = [
            {"keyword": "airpods", "limit": 3},
            {"keyword": "nintendo switch", "limit": 2}
        ]
        
        for search in test_searches:
            print(f"\n  Searching: '{search['keyword']}'")
            results = search_ebay(**search)
            
            if results:
                print(f"  ✅ Found {len(results)} results")
                
                # Show first result details
                if results:
                    item = results[0]
                    print(f"    📦 {item['title'][:50]}...")
                    print(f"    💰 ${item['price']:.2f} + ${item['shipping_cost']:.2f} shipping")
                    print(f"    🏪 Seller: {item['seller_username']} ({item['seller_feedback_percentage']:.1f}%)")
                    print(f"    📍 {item['location']}")
            else:
                print(f"  ⚠️ No results found for '{search['keyword']}'")
        
        # Test category functionality
        print("\n📂 Testing category functionality...")
        categories = get_categories()
        print(f"✅ Found {len(categories.get('categories', {}))} categories")
        
        print("\n✅ eBay API test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import eBay API module: {e}")
        print("💡 Make sure 'ebay_api_v2.py' is in the same directory")
        return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Check your eBay API credentials and internet connection")
        logger.exception("Full error details:")
        return False

def test_flask_integration():
    """Test Flask integration"""
    
    print("\n🌐 Testing Flask Integration")
    print("-" * 30)
    
    try:
        from app_v2 import app
        print("✅ Flask app imported successfully")
        
        # Test if we can create app context
        with app.app_context():
            print("✅ Flask app context works")
        
        # Test API endpoints
        client = app.test_client()
        
        # Test health endpoint
        response = client.get('/api/health')
        if response.status_code == 200:
            print("✅ /api/health endpoint works")
            health_data = json.loads(response.data)
            print(f"   Server: {health_data['data']['server']}")
            print(f"   eBay API: {'✅ Available' if health_data['data']['ebay_api_available'] else '⚠️ Demo Mode'}")
        else:
            print(f"⚠️ /api/health returned {response.status_code}")
        
        # Test categories endpoint
        response = client.get('/api/categories')
        if response.status_code == 200:
            print("✅ /api/categories endpoint works")
        else:
            print(f"⚠️ /api/categories returned {response.status_code}")
        
        # Test scan endpoint with sample data
        scan_data = {"keyword": "test", "limit": 1}
        response = client.post('/api/scan', 
                             data=json.dumps(scan_data),
                             content_type='application/json')
        if response.status_code == 200:
            print("✅ /api/scan endpoint works")
        else:
            print(f"⚠️ /api/scan returned {response.status_code}")
        
        print("💡 To test the web interface:")
        print("   1. Run: python app_v2.py")
        print("   2. Open: http://localhost:5000/search")
        print("   3. Try the eBay search functionality")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Flask test failed: {e}")
        logger.exception("Full error details:")
        return False

def test_credentials():
    """Test if eBay credentials are properly configured"""
    
    print("\n🔐 Testing eBay Credentials")
    print("-" * 30)
    
    try:
        from ebay_api_v2 import ebay_api
        
        print(f"App ID: {ebay_api.app_id}")
        print(f"Dev ID: {ebay_api.dev_id}")
        print(f"Cert ID: {ebay_api.cert_id[:10]}...")
        print(f"Sandbox Mode: {ebay_api.is_sandbox}")
        
        if ebay_api.app_id and ebay_api.dev_id and ebay_api.cert_id:
            print("✅ All credentials are configured")
            return True
        else:
            print("❌ Some credentials are missing")
            return False
            
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        return False

def main():
    """Main test function"""
    
    success = True
    
    # Test credentials
    if not test_credentials():
        success = False
    
    # Test eBay API
    if not test_ebay_api():
        success = False
    
    # Test Flask integration
    if not test_flask_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! FlipHawk is ready to use.")
        print("\n🚀 Quick Start:")
        print("1. python app_v2.py")
        print("2. Open http://localhost:5000/search")
        print("3. Start searching for eBay deals!")
        print("\n📋 Available endpoints:")
        print("   • / - Main page")
        print("   • /search - eBay search interface")
        print("   • /arbitrage - Arbitrage scanner")
        print("   • /api/health - API health check")
        print("   • /api/scan - Search eBay listings")
        print("   • /api/categories - Get categories")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Verify your eBay API credentials")
        print("2. Check your internet connection")
        print("3. Make sure all required files are present:")
        print("   - ebay_api_v2.py")
        print("   - app_v2.py")
        print("   - templates/search.html")
        print("4. Install required packages:")
        print("   pip install flask flask-cors requests")
    
    return success

if __name__ == "__main__":
    main()
