# Save this as: test_ebay_api.py

#!/usr/bin/env python3
"""
Test script for FlipHawk eBay Browse API integration
Run this to test if your eBay API credentials are working
"""

import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ebay_api():
    """Test the eBay API integration"""
    
    print("🚀 FlipHawk eBay API Test")
    print("=" * 50)
    
    try:
        # Import our eBay API module
        from ebay_api import search_ebay, EbayBrowseAPI
        
        print("✅ Successfully imported eBay API module")
        
        # Test API credentials
        api = EbayBrowseAPI(
            app_id="JackDail-FlipHawk-SBX-bf00e7bcf-34d63630",
            dev_id="f20a1274-fea2-4041-a8dc-721ecf5f38e9", 
            cert_id="SBX-f00e7bcfbabb-98f9-4d3a-bd03-5ff9",
            is_sandbox=True
        )
        
        print("✅ API client initialized")
        
        # Test getting access token
        print("\n🔑 Testing OAuth access token...")
        token = api.get_access_token()
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
        
        print("\n✅ eBay API test completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Run 'python app.py' to start the Flask server")
        print("   2. Open http://localhost:5000 in your browser")
        print("   3. Try searching for products!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import eBay API module: {e}")
        print("💡 Make sure 'ebay_api.py' is in the same directory")
        return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Check your eBay API credentials and internet connection")
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
        return False

def main():
    """Main test function"""
    
    success = True
    
    # Test eBay API
    if not test_ebay_api():
        success = False
    
    # Test Flask integration
    if not test_flask_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! FlipHawk is ready to use.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return success

if __name__ == "__main__":
    main()
