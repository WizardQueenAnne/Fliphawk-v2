#!/usr/bin/env python3
"""
Test script for FlipHawk Real-Time eBay Scraper
Run this to verify the scraper is working with real eBay data
"""

import sys
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scraper():
    """Test the real-time scraper"""
    
    print("🚀 FlipHawk Real-Time Scraper Test")
    print("=" * 50)
    print("⚠️  This will scrape REAL eBay data - NO dummy data")
    print()
    
    try:
        # Import our scraper
        from ebay_realtime_scraper import search_ebay_real, find_arbitrage_real
        
        print("✅ Successfully imported real-time scraper")
        
        # Test basic search
        print("\n🔍 Testing basic eBay search...")
        test_keyword = "airpods"
        listings = search_ebay_real(keyword=test_keyword, limit=5)
        
        if listings:
            print(f"✅ Found {len(listings)} real eBay listings")
            
            # Show first listing
            listing = listings[0]
            print(f"\n📦 Sample Listing:")
            print(f"   Title: {listing['title'][:60]}...")
            print(f"   Price: ${listing['price']:.2f}")
            print(f"   Shipping: ${listing['shipping_cost']:.2f}")
            print(f"   Total: ${listing['total_cost']:.2f}")
            print(f"   Condition: {listing['condition']}")
            print(f"   Seller: {listing['seller_username']} ({listing['seller_rating']})")
            print(f"   Link: {listing['ebay_link']}")
        else:
            print("❌ No listings found - this may indicate an issue")
            return False
        
        # Test arbitrage finding
        print(f"\n🎯 Testing arbitrage detection...")
        arbitrage_results = find_arbitrage_real(
            keyword="nintendo switch",
            min_profit=10.0,
            limit=15
        )
        
        opportunities = arbitrage_results['top_opportunities']
        print(f"✅ Arbitrage scan completed")
        print(f"   Duration: {arbitrage_results['scan_metadata']['duration_seconds']}s")
        print(f"   Listings analyzed: {arbitrage_results['scan_metadata']['total_listings_analyzed']}")
        print(f"   Opportunities found: {len(opportunities)}")
        
        if opportunities:
            opp = opportunities[0]
            print(f"\n💎 Sample Arbitrage Opportunity:")
            print(f"   Buy: ${opp['buy_listing']['total_cost']:.2f}")
            print(f"   Sell Reference: ${opp['sell_reference']['price']:.2f}")
            print(f"   Net Profit: ${opp['net_profit_after_fees']:.2f}")
            print(f"   ROI: {opp['roi_percentage']:.1f}%")
            print(f"   Confidence: {opp['confidence_score']}%")
        
        print("\n✅ Real-time scraper test PASSED!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import scraper: {e}")
        print("💡 Make sure 'ebay_realtime_scraper.py' is in the same directory")
        return False
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        logger.exception("Full error details:")
        return False

def test_flask_app():
    """Test Flask app integration"""
    
    print("\n🌐 Testing Flask App Integration")
    print("-" * 30)
    
    try:
        from app_realtime import app
        print("✅ Flask app imported successfully")
        
        # Test client
        client = app.test_client()
        
        # Test health endpoint
        response = client.get('/api/health')
        if response.status_code == 200:
            print("✅ /api/health endpoint works")
        else:
            print(f"⚠️ /api/health returned {response.status_code}")
        
        print("💡 To test the full web interface:")
        print("   1. Run: python app_realtime.py")
        print("   2. Open: http://localhost:5000")
        print("   3. Try searching for products!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Flask test failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    
    print("\n📦 Testing Dependencies")
    print("-" * 30)
    
    required_packages = [
        'requests', 'beautifulsoup4', 'flask', 'flask_cors'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'beautifulsoup4':
                import bs4
            elif package == 'flask_cors':
                import flask_cors
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All dependencies available")
        return True

def main():
    """Main test function"""
    
    success = True
    
    # Test dependencies
    if not test_dependencies():
        success = False
        print("\n❌ Install missing dependencies first!")
        return False
    
    # Test scraper
    if not test_scraper():
        success = False
    
    # Test Flask app
    if not test_flask_app():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! FlipHawk is ready for real-time arbitrage scanning.")
        print("\n🚀 QUICK START:")
        print("1. python app_realtime.py")
        print("2. Open http://localhost:5000")
        print("3. Search for arbitrage opportunities!")
        print("\n📝 NOTES:")
        print("• This scraper uses REAL eBay data")
        print("• No API keys needed")
        print("• Respects eBay's rate limits")
        print("• Finds actual price differences between listings")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Install missing dependencies")
        print("2. Check your internet connection") 
        print("3. Make sure all files are in the same directory")
        print("4. Try running the scraper test again")
    
    return success

if __name__ == "__main__":
    main()
