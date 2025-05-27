#!/usr/bin/env python3
"""
Test script for FlipHawk eBay Browse API integration
Run this to test if your eBay API credentials are working
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
        from ebay_scraper import search_ebay, api_client, get_category_keywords
        
        print("✅ Successfully imported eBay API module")
        
        # Test API credentials
        print("\n🔑 Testing OAuth access token...")
        token = api_client.get_access_token()
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
        
        # Test category keywords
        print("\n📂 Testing category keywords...")
        categories = get_category_keywords()
        print(f"✅ Found {len(categories)} categories with keyword suggestions")
        
        print("\n✅ eBay API test completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Run 'python app.py' to start the Flask server")
        print("   2. Open http://localhost:5000 in your browser")
        print("   3. Try searching for products!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import eBay API module: {e}")
        print("💡 Make sure 'ebay_scraper.py' is in the same directory")
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
        from app import app
        print("✅ Flask app imported successfully")
        
        # Test if we can create app context
        with app.app_context():
            print("✅ Flask app context works")
        
        # Test API endpoints
        client = app.test_client()
        
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
        print("   1. Run: python app.py")
        print("   2. Open: http://localhost:5000")
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
        from ebay_scraper import api_client
        
        print(f"App ID: {api_client.app_id}")
        print(f"Dev ID: {api_client.dev_id}")
        print(f"Cert ID: {api_client.cert_id[:10]}...")
        print(f"Sandbox Mode: {api_client.is_sandbox}")
        
        if api_client.app_id and api_client.dev_id and api_client.cert_id:
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
        print("1. python app.py")
        print("2. Open http://localhost:5000/ebay-search")
        print("3. Start searching for arbitrage opportunities!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Verify your eBay API credentials")
        print("2. Check your internet connection")
        print("3. Make sure all required files are present")
    
    return success

if __name__ == "__main__":
    main()
