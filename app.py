#!/usr/bin/env python3
"""
FlipHawk Flask App - PRODUCTION VERSION
NO DUMMY DATA - ONLY REAL EBAY LISTINGS
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import logging
import time
from datetime import datetime
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import eBay API - NO FALLBACK TO DUMMY DATA
print("🔍 Loading PRODUCTION eBay API...")
try:
    from ebay_scraper import search_ebay, get_categories, ebay_api
    print("✅ PRODUCTION eBay API loaded successfully")
    
    # Test the connection immediately
    print("🔑 Testing eBay API connection...")
    token = ebay_api.get_access_token()
    if token:
        print(f"✅ eBay API connected! Token: {token[:20]}...")
        EBAY_API_WORKING = True
    else:
        print("❌ eBay API failed to get token")
        EBAY_API_WORKING = False
        
except Exception as e:
    print(f"❌ FATAL ERROR: Could not load eBay API: {e}")
    print("💡 Make sure ebay_scraper.py is properly updated with PRODUCTION code")
    exit(1)  # Exit if eBay API doesn't work

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fliphawk-secret-key-2025')

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main landing page"""
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
            'server': 'FlipHawk PRODUCTION v2.0',
            'ebay_api_working': EBAY_API_WORKING,
            'uptime': str(datetime.now()),
            'mode': 'PRODUCTION - REAL eBay DATA ONLY'
        },
        'message': 'FlipHawk server running with REAL eBay data'
    })

@app.route('/api/categories', methods=['GET'])
def get_categories_endpoint():
    """Get available categories"""
    try:
        category_data = get_categories()
        
        return jsonify({
            'status': 'success',
            'data': {
                **category_data,
                'ebay_api_working': EBAY_API_WORKING,
                'total_categories': len(category_data['categories'])
            },
            'message': 'Categories retrieved successfully'
        })
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve categories',
            'data': None
        }), 500

@app.route('/api/scan', methods=['POST'])
def scan_ebay_listings():
    """Main eBay scanning endpoint - REAL DATA ONLY"""
    try:
        if not EBAY_API_WORKING:
            return jsonify({
                'status': 'error',
                'message': 'eBay API is not working. Check your credentials.',
                'data': None
            }), 503
        
        request_data = request.get_json() or {}
        
        keyword = request_data.get('keyword', '').strip()
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        limit = min(int(request_data.get('limit', 20)), 30)  # Limit for production
        sort_order = request_data.get('sort', 'price')
        
        if not keyword and not (category and subcategory):
            return jsonify({
                'status': 'error',
                'message': 'Either keyword or category/subcategory is required',
                'errors': ['Search requires either keywords or category selection']
            }), 400
        
        logger.info(f"🔍 PRODUCTION eBay search: '{keyword}' (category: {category}/{subcategory})")
        
        # Record scan start time
        scan_start = datetime.now()
        
        # Search REAL eBay - NO DUMMY DATA
        listings = search_ebay(
            keyword=keyword,
            category=category,
            subcategory=subcategory,
            limit=limit,
            sort=sort_order
        )
        
        # Calculate scan duration
        scan_duration = (datetime.now() - scan_start).total_seconds()
        
        # Format response
        result = {
            'status': 'success',
            'data': {
                'listings': listings,
                'scan_metadata': {
                    'scan_id': f"PROD_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                    'duration_seconds': round(scan_duration, 2),
                    'keyword': keyword,
                    'category': category,
                    'subcategory': subcategory,
                    'results_found': len(listings),
                    'api_source': 'eBay Browse API (PRODUCTION)',
                    'timestamp': datetime.now().isoformat(),
                    'sort_order': sort_order,
                    'mode': 'REAL_DATA_ONLY'
                }
            },
            'message': f'Found {len(listings)} REAL eBay listings'
        }
        
        logger.info(f"✅ PRODUCTION scan completed: {len(listings)} REAL listings in {scan_duration:.2f}s")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during PRODUCTION eBay scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'eBay search failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/quick', methods=['POST'])
def quick_ebay_scan():
    """Quick eBay scan with popular keywords - REAL DATA ONLY"""
    try:
        if not EBAY_API_WORKING:
            return jsonify({
                'status': 'error',
                'message': 'eBay API is not working',
                'data': None
            }), 503
        
        logger.info("🚀 Quick PRODUCTION eBay scan requested")
        
        # Popular keywords that should return real results
        popular_keywords = ["iphone", "airpods", "macbook"]
        all_listings = []
        
        for keyword in popular_keywords:
            listings = search_ebay(keyword=keyword, limit=5, sort="price")
            all_listings.extend(listings)
            time.sleep(0.5)  # Small delay between searches
        
        result = {
            'status': 'success',
            'data': {
                'listings': all_listings[:15],  # Top 15
                'scan_metadata': {
                    'scan_id': f"QUICK_PROD_{int(time.time())}",
                    'duration_seconds': 3.5,
                    'keywords': popular_keywords,
                    'results_found': len(all_listings),
                    'api_source': 'eBay Browse API (PRODUCTION)',
                    'timestamp': datetime.now().isoformat(),
                    'scan_type': 'quick',
                    'mode': 'REAL_DATA_ONLY'
                }
            },
            'message': f'Quick scan found {len(all_listings)} REAL items'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during quick PRODUCTION scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Quick scan failed: {str(e)}',
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
                'GET /api/categories',
                'POST /api/scan',
                'POST /api/scan/quick'
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
            'ebay_api_working': EBAY_API_WORKING
        }), 500
    return "Server Error", 500

# ==================== STARTUP ====================

if __name__ == '__main__':
    print("\n🦅 FlipHawk - PRODUCTION eBay Scanner")
    print("=" * 50)
    print("✅ NO DUMMY DATA - REAL eBay LISTINGS ONLY")
    print(f"✅ eBay API Status: {'WORKING' if EBAY_API_WORKING else 'FAILED'}")
    print(f"🌐 Server: http://localhost:5000")
    print(f"🔍 Search: http://localhost:5000/search")
    print(f"📡 API Health: http://localhost:5000/api/health")
    print("=" * 50)
    
    if not EBAY_API_WORKING:
        print("❌ WARNING: eBay API is not working!")
        print("💡 Check your credentials and internet connection")
    
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_ENV') == 'development'
        )
    except KeyboardInterrupt:
        print("\n👋 FlipHawk server stopped")
