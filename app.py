"""
Enhanced Flask App Integration
Updated app.py to use the enhanced scraper with better frontend integration
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import time

# Import our enhanced modules
from enhanced_scraper import (
    EnhancedFlipHawkScraper, 
    create_enhanced_api_endpoints, 
    validate_enhanced_scan_request
)
from backend.flipship.product_manager import FlipShipProductManager
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for API endpoints
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize enhanced scraper and API endpoints
enhanced_scraper = EnhancedFlipHawkScraper()
api_endpoints = create_enhanced_api_endpoints(enhanced_scraper)
flipship_manager = FlipShipProductManager()

# Global state for background scanning
background_scan_active = False
background_scan_results = None

@app.route('/')
def index():
    """Main landing page - redirect to FlipHawk"""
    return render_template('500.html'), 500

@app.errorhandler(429)
def rate_limit_error(error):
    """Handle rate limiting errors"""
    return jsonify({
        'status': 'error',
        'message': 'Rate limit exceeded. Please try again later.',
        'data': None
    }), 429

# =============================================================================
# INITIALIZATION AND STARTUP
# =============================================================================

def initialize_enhanced_app():
    """Initialize application with enhanced features"""
    try:
        # Initialize FlipShip with sample products
        flipship_manager.initialize_sample_products()
        logger.info("✅ FlipShip initialized with sample products")
        
        # Test enhanced scraper
        logger.info("🧪 Testing enhanced scraper...")
        test_result = enhanced_scraper.comprehensive_arbitrage_scan(
            keywords="test product",
            target_categories=['Tech'],
            target_subcategories={'Tech': ['Headphones']},
            min_profit=10.0,
            max_results=1
        )
        
        if test_result['opportunities_summary']['total_opportunities'] >= 0:
            logger.info("✅ Enhanced scraper test successful")
        else:
            logger.warning("⚠️ Enhanced scraper test returned no results")
            
    except Exception as e:
        logger.error(f"❌ Error during enhanced app initialization: {e}")

# Initialize when app starts
with app.app_context():
    initialize_enhanced_app()

if __name__ == '__main__':
    logger.info("🚀 Starting Enhanced FlipHawk Server...")
    logger.info("📡 Enhanced eBay scraper with advanced keyword generation")
    logger.info("🎯 Intelligent profitability analysis")
    logger.info("🔄 FlipShip integration ready")
    logger.info("🌐 Frontend available at http://localhost:5000")
    
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development',
        threaded=True  # Enable threading for background scans
    )('fliphawk_enhanced.html')

@app.route('/fliphawk')
def fliphawk():
    """Enhanced FlipHawk arbitrage scanner interface"""
    return render_template('fliphawk_enhanced.html')

@app.route('/flipship')
def flipship():
    """FlipShip storefront interface"""
    products = flipship_manager.get_featured_products()
    return render_template('flipship.html', products=products)

# =============================================================================
# ENHANCED API ROUTES
# =============================================================================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get available categories and subcategories"""
    try:
        result = api_endpoints['get_categories']()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve categories',
            'data': None
        }), 500

@app.route('/api/scan', methods=['POST'])
def scan_arbitrage():
    """Enhanced arbitrage scan with user parameters"""
    try:
        request_data = request.get_json() or {}
        
        # Validate request data
        validation = validate_enhanced_scan_request(request_data)
        if not validation['valid']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request parameters',
                'errors': validation['errors']
            }), 400
        
        # Log scan request
        logger.info(f"Starting enhanced scan with params: {request_data}")
        
        # Start enhanced scan
        result = api_endpoints['scan_arbitrage'](request_data)
        
        # Store results in session for potential FlipShip integration
        if result['status'] == 'success':
            session['last_scan_results'] = result['data']
            session['scan_timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during enhanced scan: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Enhanced scan failed due to server error',
            'data': None
        }), 500

@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Enhanced quick scan with trending keywords"""
    try:
        logger.info("Starting enhanced quick scan")
        result = api_endpoints['quick_scan']()
        
        # Store results in session
        if result['status'] == 'success':
            session['last_scan_results'] = result['data']
            session['scan_timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during enhanced quick scan: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Enhanced quick scan failed',
            'data': None
        }), 500

@app.route('/api/scan/trending', methods=['POST'])
def trending_scan():
    """Scan with current trending keywords"""
    try:
        # Get trending keywords from various sources
        trending_keywords = get_current_trending_keywords()
        
        scan_params = {
            'keywords': ', '.join(trending_keywords[:5]),
            'categories': ['Tech', 'Gaming', 'Collectibles', 'Fashion'],
            'subcategories': {
                'Tech': ['Headphones', 'Smartphones'],
                'Gaming': ['Consoles', 'Video Games'],
                'Collectibles': ['Trading Cards'],
                'Fashion': ['Sneakers']
            },
            'min_profit': 20.0,
            'max_results': 20
        }
        
        logger.info(f"Starting trending scan with keywords: {trending_keywords}")
        result = api_endpoints['scan_arbitrage'](scan_params)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during trending scan: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Trending scan failed',
            'data': None
        }), 500

@app.route('/api/scan/keyword-suggestions', methods=['GET'])
def get_keyword_suggestions():
    """Get keyword suggestions for user input"""
    try:
        query = request.args.get('q', '').lower()
        category = request.args.get('category', 'all').lower()
        
        # Load keyword suggestions from various sources
        suggestions = generate_keyword_suggestions(query, category)
        
        return jsonify({
            'status': 'success',
            'data': {
                'suggestions': suggestions[:10],  # Limit to 10 suggestions
                'query': query,
                'category': category
            },
            'message': 'Keyword suggestions retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting keyword suggestions: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get keyword suggestions',
            'data': None
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_session_stats():
    """Get current session statistics"""
    try:
        result = api_endpoints['get_session_stats']()
        
        # Add additional stats
        if result['status'] == 'success':
            # Get last scan info from session
            last_scan = session.get('last_scan_results')
            if last_scan:
                result['data']['last_scan'] = {
                    'timestamp': session.get('scan_timestamp'),
                    'opportunities_found': last_scan.get('opportunities_summary', {}).get('total_opportunities', 0),
                    'average_profit': last_scan.get('opportunities_summary', {}).get('average_profit', 0)
                }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve session stats',
            'data': None
        }), 500

# =============================================================================
# ENHANCED FLIPSHIP API ROUTES
# =============================================================================

@app.route('/api/flipship/products', methods=['GET'])
def get_flipship_products():
    """Get FlipShip product catalog"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category', 'all')
        
        products = flipship_manager.get_products(
            page=page, 
            limit=limit, 
            category=category
        )
        
        return jsonify({
            'status': 'success',
            'data': products,
            'message': 'Products retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting FlipShip products: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve products',
            'data': None
        }), 500

@app.route('/api/flipship/create', methods=['POST'])
def create_flipship_product():
    """Create new FlipShip product from scan results"""
    try:
        request_data = request.get_json() or {}
        opportunity_id = request_data.get('opportunity_id')
        
        if not opportunity_id:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity ID required',
                'data': None
            }), 400
        
        # Get the opportunity from last scan results
        last_scan = session.get('last_scan_results')
        if not last_scan:
            return jsonify({
                'status': 'error',
                'message': 'No recent scan results found',
                'data': None
            }), 400
        
        # Find the specific opportunity
        opportunity_data = None
        for opp in last_scan.get('top_opportunities', []):
            if opp.get('item_id') == opportunity_id:
                opportunity_data = opp
                break
        
        if not opportunity_data:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity not found in recent results',
                'data': None
            }), 400
        
        # Create FlipShip product
        product = flipship_manager.create_product_from_opportunity(opportunity_data)
        
        return jsonify({
            'status': 'success',
            'data': product.__dict__ if hasattr(product, '__dict__') else product,
            'message': 'Product created successfully for FlipShip'
        })
        
    except Exception as e:
        logger.error(f"Error creating FlipShip product: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to create product: {str(e)}',
            'data': None
        }), 500

@app.route('/api/flipship/bulk-create', methods=['POST'])
def bulk_create_flipship_products():
    """Create multiple FlipShip products from scan results"""
    try:
        request_data = request.get_json() or {}
        opportunity_ids = request_data.get('opportunity_ids', [])
        
        if not opportunity_ids:
            return jsonify({
                'status': 'error',
                'message': 'At least one opportunity ID required',
                'data': None
            }), 400
        
        # Get last scan results
        last_scan = session.get('last_scan_results')
        if not last_scan:
            return jsonify({
                'status': 'error',
                'message': 'No recent scan results found',
                'data': None
            }), 400
        
        created_products = []
        failed_products = []
        
        for opp_id in opportunity_ids:
            try:
                # Find opportunity
                opportunity_data = None
                for opp in last_scan.get('top_opportunities', []):
                    if opp.get('item_id') == opp_id:
                        opportunity_data = opp
                        break
                
                if opportunity_data:
                    product = flipship_manager.create_product_from_opportunity(opportunity_data)
                    created_products.append({
                        'opportunity_id': opp_id,
                        'product_id': product.product_id,
                        'title': product.title
                    })
                else:
                    failed_products.append({
                        'opportunity_id': opp_id,
                        'error': 'Opportunity not found'
                    })
                    
            except Exception as e:
                failed_products.append({
                    'opportunity_id': opp_id,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'data': {
                'created_products': created_products,
                'failed_products': failed_products,
                'total_created': len(created_products),
                'total_failed': len(failed_products)
            },
            'message': f'Bulk creation completed: {len(created_products)} created, {len(failed_products)} failed'
        })
        
    except Exception as e:
        logger.error(f"Error in bulk creation: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Bulk creation failed: {str(e)}',
            'data': None
        }), 500

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_current_trending_keywords():
    """Get current trending keywords from various sources"""
    # This could be enhanced to pull from actual trending APIs
    base_trending = [
        "viral tiktok", "trending 2025", "popular now", "hot deals",
        "limited edition", "exclusive drop", "sold out everywhere",
        "rare find", "collector item", "investment piece",
        "airpods pro 2", "nintendo switch oled", "pokemon cards",
        "supreme hoodie", "jordan 1", "iphone 15 pro", "ps5",
        "tesla accessories", "crypto merch", "nft collectibles"
    ]
    
    # Add seasonal/time-based keywords
    current_month = datetime.now().month
    seasonal_keywords = {
        1: ["new year", "resolution", "fitness"],
        2: ["valentine", "love", "gifts"],
        3: ["spring", "easter", "renewal"],
        4: ["april", "spring cleaning", "fresh"],
        5: ["mother's day", "graduation", "spring"],
        6: ["summer", "vacation", "outdoor"],
        7: ["summer", "july 4th", "patriotic"],
        8: ["back to school", "college", "supplies"],
        9: ["fall", "autumn", "cozy"],
        10: ["halloween", "spooky", "costume"],
        11: ["thanksgiving", "black friday", "deals"],
        12: ["christmas", "holiday", "gifts"]
    }
    
    seasonal = seasonal_keywords.get(current_month, [])
    
    return base_trending + seasonal

def generate_keyword_suggestions(query, category):
    """Generate keyword suggestions based on user input"""
    keyword_database = {
        'tech': [
            'airpods', 'iphone', 'samsung galaxy', 'macbook', 'ipad',
            'gaming laptop', 'mechanical keyboard', 'wireless mouse',
            'bluetooth speaker', 'smartwatch', 'camera', 'headphones'
        ],
        'gaming': [
            'ps5', 'xbox series x', 'nintendo switch', 'gaming chair',
            'gaming headset', 'controller', 'gaming monitor', 'pc parts',
            'call of duty', 'pokemon', 'zelda', 'mario', 'fifa'
        ],
        'collectibles': [
            'pokemon cards', 'magic cards', 'baseball cards', 'funko pop',
            'action figures', 'vintage toys', 'comic books', 'trading cards',
            'graded cards', 'psa 10', 'first edition', 'rare cards'
        ],
        'fashion': [
            'jordan', 'yeezy', 'supreme', 'nike', 'adidas', 'designer',
            'sneakers', 'streetwear', 'vintage', 'luxury', 'limited edition',
            'off white', 'balenciaga', 'gucci', 'louis vuitton'
        ],
        'all': []
    }
    
    # Get category keywords
    category_keywords = keyword_database.get(category, keyword_database['all'])
    
    # If no category specified, use all keywords
    if category == 'all' or not category_keywords:
        all_keywords = []
        for cat_kw in keyword_database.values():
            all_keywords.extend(cat_kw)
        category_keywords = all_keywords
    
    # Filter keywords based on query
    if query:
        suggestions = [kw for kw in category_keywords if query in kw.lower()]
        # Add query variations
        suggestions.extend([
            f"{query} new", f"{query} used", f"{query} vintage",
            f"{query} rare", f"{query} limited", f"authentic {query}"
        ])
    else:
        suggestions = category_keywords[:10]
    
    return list(set(suggestions))  # Remove duplicates

# =============================================================================
# BACKGROUND SCANNING (Enhanced)
# =============================================================================

@app.route('/api/scan/background/start', methods=['POST'])
def start_background_scan():
    """Start enhanced continuous background scanning"""
    global background_scan_active
    
    if background_scan_active:
        return jsonify({
            'status': 'info',
            'message': 'Background scan already running',
            'data': {'active': True}
        })
    
    def enhanced_background_scan_worker():
        global background_scan_active, background_scan_results
        background_scan_active = True
        
        scan_count = 0
        while background_scan_active:
            try:
                # Rotate through different scan types
                if scan_count % 3 == 0:
                    # Trending scan
                    trending_keywords = get_current_trending_keywords()
                    scan_params = {
                        'keywords': ', '.join(trending_keywords[:3]),
                        'categories': ['Tech', 'Gaming'],
                        'min_profit': 30.0,
                        'max_results': 10
                    }
                elif scan_count % 3 == 1:
                    # Tech focus scan
                    scan_params = {
                        'keywords': 'airpods, iphone, macbook, gaming laptop',
                        'categories': ['Tech'],
                        'subcategories': {'Tech': ['Headphones', 'Smartphones', 'Laptops']},
                        'min_profit': 25.0,
                        'max_results': 10
                    }
                else:
                    # Collectibles focus scan
                    scan_params = {
                        'keywords': 'pokemon cards, magic cards, funko pop',
                        'categories': ['Collectibles'],
                        'subcategories': {'Collectibles': ['Trading Cards', 'Action Figures']},
                        'min_profit': 35.0,
                        'max_results': 10
                    }
                
                logger.info(f"Running background scan #{scan_count + 1}...")
                result = api_endpoints['scan_arbitrage'](scan_params)
                background_scan_results = {
                    'scan_number': scan_count + 1,
                    'timestamp': datetime.now().isoformat(),
                    'result': result
                }
                
                scan_count += 1
                
                # Wait 10 minutes before next scan
                for _ in range(600):  # 600 seconds = 10 minutes
                    if not background_scan_active:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Background scan error: {e}")
                time.sleep(120)  # Wait 2 minutes on error
        
        logger.info("Background scanning stopped")
    
    # Start background thread
    thread = threading.Thread(target=enhanced_background_scan_worker, daemon=True)
    thread.start()
    
    return jsonify({
        'status': 'success',
        'message': 'Enhanced background scan started',
        'data': {'active': True}
    })

@app.route('/api/scan/background/stop', methods=['POST'])
def stop_background_scan():
    """Stop background scanning"""
    global background_scan_active
    background_scan_active = False
    
    return jsonify({
        'status': 'success',
        'message': 'Background scan stopped',
        'data': {'active': False}
    })

@app.route('/api/scan/background/status', methods=['GET'])
def get_background_scan_status():
    """Get background scan status and latest results"""
    return jsonify({
        'status': 'success',
        'data': {
            'active': background_scan_active,
            'latest_results': background_scan_results
        },
        'message': 'Background scan status retrieved'
    })

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'API endpoint not found',
            'data': None
        }), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'data': None
        }), 500
    return render_template
