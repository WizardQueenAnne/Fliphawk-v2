#!/usr/bin/env python3
"""
FlipHawk Flask App - REAL-TIME SCRAPING VERSION
Uses web scraping for REAL eBay data - NO API needed, NO dummy data
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import logging
import time
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our real-time scraper
try:
    from ebay_realtime_scraper import search_ebay_real, find_arbitrage_real, scraper
    print("✅ Real-time eBay scraper loaded successfully")
    SCRAPER_AVAILABLE = True
except Exception as e:
    print(f"❌ Failed to load scraper: {e}")
    SCRAPER_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fliphawk-realtime-key-2025')

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main arbitrage scanner page"""
    return render_template('index.html')

@app.route('/search')
def search_page():
    """eBay search interface"""
    return render_template('ebay_search.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'data': {
            'server': 'FlipHawk Real-Time Scraper v1.0',
            'scraper_available': SCRAPER_AVAILABLE,
            'uptime': str(datetime.now()),
            'mode': 'REAL-TIME WEB SCRAPING',
            'no_dummy_data': True
        },
        'message': 'FlipHawk server running with real-time eBay scraping'
    })

@app.route('/api/scan', methods=['POST'])
def scan_arbitrage():
    """Main arbitrage scanning endpoint - REAL eBay data only"""
    try:
        if not SCRAPER_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'Real-time scraper is not available',
                'data': None
            }), 503
        
        request_data = request.get_json() or {}
        
        # Handle multiple possible keyword fields
        keyword = request_data.get('keyword', '').strip()
        keywords = request_data.get('keywords', '').strip()
        search_term = keyword or keywords
        
        # If no direct keyword, check if category data is provided
        if not search_term:
            category = request_data.get('category', '').strip()
            subcategory = request_data.get('subcategory', '').strip()
            
            # Use category as search term if provided
            if category:
                search_term = category
            elif subcategory:
                search_term = subcategory
        
        # Final validation
        if not search_term:
            return jsonify({
                'status': 'error',
                'message': 'Search keyword is required',
                'errors': ['Please provide a keyword to search for']
            }), 400
        
        limit = min(int(request_data.get('limit', 20)), 50)  # Cap at 50 for performance
        min_profit = float(request_data.get('min_profit', 15.0))
        
        logger.info(f"🔍 Real-time arbitrage scan: '{search_term}' (min profit: ${min_profit})")
        
        # Record scan start time
        scan_start = datetime.now()
        
        # Search for REAL arbitrage opportunities
        results = find_arbitrage_real(
            keyword=search_term,
            min_profit=min_profit,
            limit=limit
        )
        
        # Calculate scan duration
        scan_duration = (datetime.now() - scan_start).total_seconds()
        
        # Update scan metadata with actual duration
        results['scan_metadata']['duration_seconds'] = round(scan_duration, 2)
        results['scan_metadata']['search_term'] = search_term
        results['scan_metadata']['min_profit_threshold'] = min_profit
        
        logger.info(f"✅ Real-time scan completed: {results['opportunities_summary']['total_opportunities']} opportunities found in {scan_duration:.2f}s")
        
        return jsonify({
            'status': 'success',
            'data': results,
            'message': f'Found {results["opportunities_summary"]["total_opportunities"]} real arbitrage opportunities'
        })
        
    except Exception as e:
        logger.error(f"Error during real-time arbitrage scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Arbitrage scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/search', methods=['POST'])
def search_ebay_listings():
    """Search eBay listings endpoint - for basic listing search"""
    try:
        if not SCRAPER_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'Real-time scraper is not available',
                'data': None
            }), 503
        
        request_data = request.get_json() or {}
        
        # Handle multiple possible keyword fields
        keyword = request_data.get('keyword', '').strip()
        keywords = request_data.get('keywords', '').strip()
        search_term = keyword or keywords
        
        # If no direct keyword, check if category data is provided
        if not search_term:
            category = request_data.get('category', '').strip()
            subcategory = request_data.get('subcategory', '').strip()
            
            # Use category as search term if provided
            if category:
                search_term = category
            elif subcategory:
                search_term = subcategory
        
        # Final validation
        if not search_term:
            return jsonify({
                'status': 'error',
                'message': 'Search keyword is required',
                'data': None
            }), 400
        
        limit = min(int(request_data.get('limit', 20)), 50)
        sort_order = request_data.get('sort', 'price')
        
        logger.info(f"🔍 Real-time eBay search: '{search_term}'")
        
        # Search for REAL listings
        listings = search_ebay_real(
            keyword=search_term,
            limit=limit,
            sort=sort_order
        )
        
        result = {
            'scan_metadata': {
                'scan_id': f"SEARCH_{int(time.time())}",
                'timestamp': datetime.now().isoformat(),
                'search_term': search_term,
                'total_listings_found': len(listings),
                'sort_order': sort_order,
                'api_source': 'Real-Time Web Scraping',
                'mode': 'LIVE_EBAY_DATA'
            },
            'listings': listings
        }
        
        logger.info(f"✅ Real-time search completed: {len(listings)} listings found")
        
        return jsonify({
            'status': 'success',
            'data': result,
            'message': f'Found {len(listings)} real eBay listings'
        })
        
    except Exception as e:
        logger.error(f"Error during real-time eBay search: {e}")
        return jsonify({
            'status': 'error',
            'message': f'eBay search failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/quick-scan', methods=['POST'])
def quick_arbitrage_scan():
    """Quick arbitrage scan with popular keywords"""
    try:
        if not SCRAPER_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'Real-time scraper is not available',
                'data': None
            }), 503
        
        logger.info("🚀 Quick real-time arbitrage scan")
        
        # Popular keywords that often have arbitrage opportunities
        popular_keyword = "airpods pro"
        
        results = find_arbitrage_real(
            keyword=popular_keyword,
            min_profit=20.0,
            limit=15
        )
        
        # Update metadata
        results['scan_metadata']['scan_type'] = 'quick'
        results['scan_metadata']['search_term'] = popular_keyword
        
        return jsonify({
            'status': 'success',
            'data': results,
            'message': f'Quick scan found {results["opportunities_summary"]["total_opportunities"]} real opportunities'
        })
        
    except Exception as e:
        logger.error(f"Error during quick real-time scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Quick scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/trending-scan', methods=['POST'])
def trending_arbitrage_scan():
    """Trending arbitrage scan with viral keywords"""
    try:
        if not SCRAPER_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'Real-time scraper is not available',
                'data': None
            }), 503
        
        logger.info("📈 Trending real-time arbitrage scan")
        
        trending_keyword = "nintendo switch oled"
        
        results = find_arbitrage_real(
            keyword=trending_keyword,
            min_profit=25.0,
            limit=20
        )
        
        # Update metadata
        results['scan_metadata']['scan_type'] = 'trending'
        results['scan_metadata']['search_term'] = trending_keyword
        
        return jsonify({
            'status': 'success',
            'data': results,
            'message': f'Trending scan found {results["opportunities_summary"]["total_opportunities"]} real opportunities'
        })
        
    except Exception as e:
        logger.error(f"Error during trending real-time scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Trending scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get suggested categories and keywords"""
    try:
        categories = {
            'categories': {
                'Tech': ['Headphones', 'Smartphones', 'Laptops', 'Tablets'],
                'Gaming': ['Consoles', 'Video Games', 'Accessories'],
                'Collectibles': ['Trading Cards', 'Action Figures', 'Coins'],
                'Fashion': ['Sneakers', 'Designer Items', 'Watches']
            },
            'suggested_keywords': {
                'High Success Rate': [
                    'airpods pro', 'nintendo switch', 'pokemon cards',
                    'iphone 14', 'macbook', 'ps5', 'xbox series x'
                ],
                'Popular Searches': [
                    'beats headphones', 'samsung galaxy', 'ipad',
                    'jordan sneakers', 'supreme', 'rolex watch'
                ],
                'Trending Now': [
                    'viral tiktok products', 'trending 2025',
                    'limited edition', 'rare collectibles'
                ]
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': categories,
            'message': 'Categories and keywords retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve categories',
            'data': None
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error', 
            'message': 'API endpoint not found',
            'available_endpoints': [
                'GET /api/health',
                'POST /api/scan',
                'POST /api/search', 
                'POST /api/quick-scan',
                'POST /api/trending-scan',
                'GET /api/categories'
            ]
        }), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error',
            'scraper_available': SCRAPER_AVAILABLE
        }), 500
    return "Server Error", 500

# ==================== STARTUP ====================

if __name__ == '__main__':
    print("\n🦅 FlipHawk - Real-Time eBay Arbitrage Scanner")
    print("=" * 60)
    print("✅ REAL-TIME WEB SCRAPING - NO DUMMY DATA")
    print("✅ NO API KEYS NEEDED - DIRECT eBay SCRAPING")
    print(f"✅ Scraper Status: {'AVAILABLE' if SCRAPER_AVAILABLE else 'UNAVAILABLE'}")
    print(f"🌐 Server: http://localhost:5000")
    print(f"🔍 Arbitrage Scanner: http://localhost:5000")
    print(f"📦 eBay Search: http://localhost:5000/search")
    print(f"📡 API Health: http://localhost:5000/api/health")
    print("=" * 60)
    
    if not SCRAPER_AVAILABLE:
        print("❌ WARNING: Real-time scraper is not available!")
        print("💡 Make sure ebay_realtime_scraper.py is in the same directory")
    else:
        print("🎯 Ready to find real arbitrage opportunities!")
    
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_ENV') == 'development'
        )
    except KeyboardInterrupt:
        print("\n👋 FlipHawk server stopped")
