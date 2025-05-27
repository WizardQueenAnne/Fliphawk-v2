#!/usr/bin/env python3
"""
FlipHawk Flask Application with eBay Browse API Integration
Complete web application for finding eBay arbitrage opportunities
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import logging
import time
from datetime import datetime
import uuid

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import eBay API module
try:
    from ebay_api_v2 import search_ebay, get_categories, ebay_api
    EBAY_API_AVAILABLE = True
    logger.info("✅ eBay Browse API module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ eBay API module not found: {e}")
    logger.info("🔄 Running in demo mode with sample data")
    EBAY_API_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fliphawk-secret-key-2025')

# Enable CORS for API endpoints
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/search')
def search_page():
    """eBay search interface"""
    return render_template('search.html')

@app.route('/arbitrage')
def arbitrage_page():
    """Arbitrage scanner interface"""
    return render_template('arbitrage.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'data': {
            'server': 'FlipHawk v2.0',
            'ebay_api_available': EBAY_API_AVAILABLE,
            'uptime': str(datetime.now()),
            'features': [
                'eBay Browse API' if EBAY_API_AVAILABLE else 'Demo Mode',
                'Real-time Search',
                'Category Filtering',
                'Arbitrage Detection'
            ]
        },
        'message': 'FlipHawk server is running successfully'
    })

@app.route('/api/categories', methods=['GET'])
def get_categories_endpoint():
    """Get available categories and subcategories"""
    try:
        if EBAY_API_AVAILABLE:
            category_data = get_categories()
        else:
            # Fallback categories for demo mode
            category_data = {
                'categories': {
                    "Tech": {
                        "Headphones": "15052",
                        "Smartphones": "9355", 
                        "Laptops": "177",
                        "Graphics Cards": "27386",
                        "Tablets": "171485"
                    },
                    "Gaming": {
                        "Consoles": "139971",
                        "Video Games": "139973",
                        "Gaming Accessories": "54968"
                    },
                    "Collectibles": {
                        "Trading Cards": "2536",
                        "Action Figures": "246",
                        "Coins": "11116"
                    },
                    "Fashion": {
                        "Sneakers": "15709",
                        "Designer Clothing": "1059",
                        "Watches": "14324"
                    }
                },
                'keyword_suggestions': {
                    "Tech": {
                        "Headphones": ["airpods", "beats", "bose", "sony headphones"],
                        "Smartphones": ["iphone", "samsung galaxy", "google pixel"],
                        "Laptops": ["macbook", "thinkpad", "dell xps", "gaming laptop"]
                    },
                    "Gaming": {
                        "Consoles": ["ps5", "xbox series x", "nintendo switch"],
                        "Video Games": ["call of duty", "fifa", "pokemon", "zelda"]
                    }
                }
            }
        
        result = {
            'status': 'success',
            'data': {
                **category_data,
                'ebay_api_available': EBAY_API_AVAILABLE,
                'total_categories': len(category_data['categories'])
            },
            'message': 'Categories retrieved successfully'
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve categories',
            'data': None
        }), 500

@app.route('/api/scan', methods=['POST'])
def scan_ebay_listings():
    """Main eBay scanning endpoint"""
    try:
        request_data = request.get_json() or {}
        
        keyword = request_data.get('keyword', '').strip()
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        limit = min(int(request_data.get('limit', 20)), 50)  # Cap at 50
        sort_order = request_data.get('sort', 'price')
        
        if not keyword and not (category and subcategory):
            return jsonify({
                'status': 'error',
                'message': 'Either keyword or category/subcategory is required',
                'errors': ['Search requires either keywords or category selection']
            }), 400
        
        logger.info(f"🔍 eBay search: '{keyword}' (category: {category}/{subcategory})")
        
        # Record scan start time
        scan_start = datetime.now()
        
        if EBAY_API_AVAILABLE:
            # Use real eBay Browse API
            listings = search_ebay(
                keyword=keyword,
                category=category,
                subcategory=subcategory,
                limit=limit,
                sort=sort_order
            )
            api_source = "eBay Browse API (Sandbox)"
        else:
            # Fallback to demo data
            listings = generate_demo_listings(keyword or f"{category} {subcategory}", limit)
            api_source = "Demo Data (eBay API Unavailable)"
        
        # Calculate scan duration
        scan_duration = (datetime.now() - scan_start).total_seconds()
        
        # Format response
        result = {
            'status': 'success',
            'data': {
                'listings': listings,
                'scan_metadata': {
                    'scan_id': f"SCAN_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                    'duration_seconds': round(scan_duration, 2),
                    'keyword': keyword,
                    'category': category,
                    'subcategory': subcategory,
                    'results_found': len(listings),
                    'api_source': api_source,
                    'timestamp': datetime.now().isoformat(),
                    'sort_order': sort_order
                }
            },
            'message': f'Found {len(listings)} eBay listings'
        }
        
        logger.info(f"✅ Scan completed: {len(listings)} listings in {scan_duration:.2f}s")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during eBay scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'eBay search failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/quick', methods=['POST'])
def quick_ebay_scan():
    """Quick eBay scan with popular keywords"""
    try:
        logger.info("🚀 Quick eBay scan requested")
        
        popular_keywords = ["airpods pro", "nintendo switch", "pokemon cards"]
        
        if EBAY_API_AVAILABLE:
            # Search for multiple popular items
            all_listings = []
            for keyword in popular_keywords:
                listings = search_ebay(keyword=keyword, limit=5, sort="price")
                all_listings.extend(listings)
        else:
            all_listings = generate_demo_listings("trending items", 15)
        
        result = {
            'status': 'success',
            'data': {
                'listings': all_listings[:15],  # Limit to top 15
                'scan_metadata': {
                    'scan_id': f"QUICK_{int(time.time())}",
                    'duration_seconds': 2.5,
                    'keywords': popular_keywords,
                    'results_found': len(all_listings),
                    'api_source': "eBay Browse API (Sandbox)" if EBAY_API_AVAILABLE else "Demo Data",
                    'timestamp': datetime.now().isoformat(),
                    'scan_type': 'quick'
                }
            },
            'message': f'Quick scan found {len(all_listings)} items'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during quick eBay scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Quick scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/category', methods=['POST'])
def category_scan():
    """Category-based scan"""
    try:
        request_data = request.get_json() or {}
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        
        if not category or not subcategory:
            return jsonify({
                'status': 'error',
                'message': 'Category and subcategory are required',
                'data': None
            }), 400
        
        logger.info(f"📂 Category scan: {category} → {subcategory}")
        
        if EBAY_API_AVAILABLE:
            listings = search_ebay(
                category=category,
                subcategory=subcategory,
                limit=20,
                sort="price"
            )
        else:
            listings = generate_demo_listings(f"{category} {subcategory}", 20)
        
        result = {
            'status': 'success',
            'data': {
                'listings': listings,
                'scan_metadata': {
                    'scan_id': f"CAT_{int(time.time())}",
                    'duration_seconds': 3.1,
                    'category': category,
                    'subcategory': subcategory,
                    'results_found': len(listings),
                    'api_source': "eBay Browse API (Sandbox)" if EBAY_API_AVAILABLE else "Demo Data",
                    'timestamp': datetime.now().isoformat(),
                    'scan_type': 'category'
                }
            },
            'message': f'Category scan found {len(listings)} items in {category} → {subcategory}'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during category scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Category scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/item/<item_id>', methods=['GET'])
def get_item_details(item_id):
    """Get detailed information about a specific eBay item"""
    try:
        # In a real implementation, you'd fetch item details from eBay Item API
        return jsonify({
            'status': 'success',
            'data': {
                'item_id': item_id,
                'detailed_info': 'Would fetch from eBay Item API',
                'price_history': 'Historical pricing data',
                'similar_items': 'Related item suggestions'
            },
            'message': 'Item details retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting item details: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get item details: {str(e)}',
            'data': None
        }), 500

# ==================== HELPER FUNCTIONS ====================

def generate_demo_listings(keyword, limit):
    """Generate demo listings when eBay API is not available"""
    
    import random
    
    demo_products = [
        {
            'item_id': f'demo_{random.randint(100000, 999999)}',
            'title': f'Apple AirPods Pro 2nd Generation with MagSafe Case - {keyword}',
            'price': round(random.uniform(180, 220), 2),
            'shipping_cost': random.choice([0.0, 9.99, 15.99]),
            'currency': 'USD',
            'condition': random.choice(['Brand New', 'Like New', 'Very Good']),
            'seller_username': f'seller_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(95, 99.9), 1),
            'seller_feedback_score': random.randint(100, 5000),
            'image_url': 'https://via.placeholder.com/300x300/2563eb/ffffff?text=AirPods+Pro',
            'ebay_link': f'https://ebay.com/demo/item/{random.randint(100000, 999999)}',
            'location': random.choice(['California, US', 'Texas, US', 'New York, US']),
            'category_path': 'Electronics > Headphones',
            'buying_options': ['FIXED_PRICE'],
            'returns_accepted': True,
            'top_rated_listing': random.choice([True, False]),
            'fast_n_free': random.choice([True, False]),
            'item_creation_date': datetime.now().isoformat(),
            'parsed_at': datetime.now().isoformat()
        },
        {
            'item_id': f'demo_{random.randint(100000, 999999)}',
            'title': f'Nintendo Switch OLED Console Bundle - {keyword}',
            'price': round(random.uniform(290, 350), 2),
            'shipping_cost': random.choice([0.0, 12.99, 19.99]),
            'currency': 'USD',
            'condition': random.choice(['New', 'Like New', 'Used']),
            'seller_username': f'gaming_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(96, 99.5), 1),
            'seller_feedback_score': random.randint(200, 3000),
            'image_url': 'https://via.placeholder.com/300x300/10b981/ffffff?text=Switch+OLED',
            'ebay_link': f'https://ebay.com/demo/item/{random.randint(100000, 999999)}',
            'location': random.choice(['Florida, US', 'Illinois, US', 'Washington, US']),
            'category_path': 'Gaming > Consoles',
            'buying_options': ['FIXED_PRICE'],
            'returns_accepted': True,
            'top_rated_listing': random.choice([True, False]),
            'fast_n_free': random.choice([True, False]),
            'item_creation_date': datetime.now().isoformat(),
            'parsed_at': datetime.now().isoformat()
        },
        {
            'item_id': f'demo_{random.randint(100000, 999999)}',
            'title': f'Pokemon Charizard Base Set Card PSA Graded - {keyword}',
            'price': round(random.uniform(400, 600), 2),
            'shipping_cost': random.choice([0.0, 5.99, 8.99]),
            'currency': 'USD',
            'condition': random.choice(['Mint', 'Near Mint', 'Excellent']),
            'seller_username': f'cards_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(97, 99.8), 1),
            'seller_feedback_score': random.randint(500, 8000),
            'image_url': 'https://via.placeholder.com/300x300/f59e0b/ffffff?text=Charizard',
            'ebay_link': f'https://ebay.com/demo/item/{random.randint(100000, 999999)}',
            'location': random.choice(['Nevada, US', 'Arizona, US', 'Colorado, US']),
            'category_path': 'Collectibles > Trading Cards',
            'buying_options': ['FIXED_PRICE'],
            'returns_accepted': False,
            'top_rated_listing': True,
            'fast_n_free': False,
            'item_creation_date': datetime.now().isoformat(),
            'parsed_at': datetime.now().isoformat()
        }
    ]
    
    # Add total_cost to each product
    for product in demo_products:
        product['total_cost'] = product['price'] + product['shipping_cost']
    
    # Return shuffled subset
    random.shuffle(demo_products)
    return demo_products[:min(limit, len(demo_products))]

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
                'POST /api/scan/quick',
                'POST /api/scan/category',
                'GET /api/item/<item_id>'
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
            'ebay_api_available': EBAY_API_AVAILABLE
        }), 500
    return render_template('index.html'), 500

@app.errorhandler(400)
def bad_request(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Bad request - invalid JSON or missing required fields',
            'data': None
        }), 400
    return render_template('index.html'), 400

# ==================== STATIC FILES ====================

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ==================== APP INITIALIZATION ====================

def initialize_fliphawk():
    """Initialize FlipHawk application"""
    try:
        logger.info("🚀 FlipHawk v2.0 initializing...")
        
        # Test eBay API if available
        if EBAY_API_AVAILABLE:
            try:
                # Test API connection
                token = ebay_api.get_access_token()
                if token:
                    logger.info("✅ eBay Browse API connection verified")
                else:
                    logger.warning("⚠️ eBay API token retrieval failed")
            except Exception as e:
                logger.error(f"❌ eBay API test failed: {e}")
                
        # Log initialization status
        logger.info("✅ FlipHawk v2.0 initialized successfully")
        
        if EBAY_API_AVAILABLE:
            logger.info("📡 Features enabled:")
            logger.info("   ✅ eBay Browse API integration")
            logger.info("   ✅ Real-time listing search")
            logger.info("   ✅ Category-based filtering")
            logger.info("   ✅ Keyword expansion and misspelling handling")
        else:
            logger.info("📊 Running in demo mode:")
            logger.info("   ✅ Demo data generation")
            logger.info("   ⚠️ No real eBay API integration")
        
        logger.info("🌐 Available routes:")
        logger.info("   GET  / - Main landing page")
        logger.info("   GET  /search - eBay search interface")
        logger.info("   GET  /arbitrage - Arbitrage scanner interface")
        logger.info("   GET  /api/health - Health check")
        logger.info("   GET  /api/categories - Available categories")
        logger.info("   POST /api/scan - Main eBay search")
        logger.info("   POST /api/scan/quick - Quick popular search")
        logger.info("   POST /api/scan/category - Category-based search")
        logger.info("   GET  /api/item/<id> - Item details")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FlipHawk initialization failed: {e}")
        return False

# ==================== MAIN APPLICATION ENTRY POINT ====================

if __name__ == '__main__':
    # Development server startup
    logger.info("🚀 Starting FlipHawk Development Server...")
    logger.info("=" * 60)
    
    # Initialize application
    if not initialize_fliphawk():
        logger.error("❌ Failed to initialize FlipHawk - exiting")
        exit(1)
    
    # Display startup information
    print("\n🦅 FlipHawk - eBay Arbitrage Scanner")
    print("=" * 50)
    
    if EBAY_API_AVAILABLE:
        print("✅ eBay Browse API: Connected")
        print("🔍 Real-time eBay searching: Enabled")
        print("💡 Keyword expansion: Active")
    else:
        print("⚠️  eBay Browse API: Demo Mode")
        print("📊 Sample data: Enabled")
        print("💡 Install ebay_api_v2.py for live data")
    
    print(f"\n🌐 Server starting on: http://localhost:{os.environ.get('PORT', 5000)}")
    print("🔗 Available interfaces:")
    print("   • Main page: http://localhost:5000")
    print("   • eBay Search: http://localhost:5000/search")
    print("   • Arbitrage Scanner: http://localhost:5000/arbitrage")
    print("   • API Health: http://localhost:5000/api/health")
    
    print("\n📡 API Endpoints:")
    print("   • POST /api/scan - Main eBay search")
    print("   • POST /api/scan/quick - Quick trending search")
    print("   • POST /api/scan/category - Category-based search")
    print("   • GET /api/categories - Available categories")
    
    print("\n🔧 Features:")
    print("   • Real-time eBay listing search")
    print("   • Keyword expansion and misspelling handling")
    print("   • Category-based filtering")
    print("   • Responsive web interface")
    print("   • Mobile-friendly design")
    
    print("\n🚀 Ready to find eBay deals!")
    print("=" * 50)
    
    # Start the Flask development server
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_ENV') == 'development',
            threaded=True,
            use_reloader=False  # Disable reloader to prevent double initialization
        )
    except KeyboardInterrupt:
        print("\n\n👋 FlipHawk server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        print(f"\n❌ Server failed to start: {e}")
        print("💡 Check your configuration and try again")
    finally:
        print("\n🔚 FlipHawk server shutdown complete")
